#!/usr/bin/env python3
"""
BMA Admin Review Server
Run: python approve.py
Serves at http://localhost:8080

Endpoints:
  GET  /api/reviews              -> returns data/reviewed_financials.json
  POST /api/save                 -> merge body into reviewed_financials.json (status=draft)
  POST /api/approve              -> merge body (status=approved), regenerate dashboard, git push
  POST /api/bot/query            -> ask bot question about company
  POST /api/bot/analyze          -> deep company analysis
  POST /api/bot/compare          -> compare companies
  POST /api/auditor/validate     -> validate financial data
  GET  /api/auditor/logs         -> fetch audit trail
  POST /api/fcr/upload           -> upload FCR document
  GET  *                         -> serve static files from repo root
"""
import json
import os
import subprocess
import uuid
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone
from urllib.parse import urlparse, parse_qs
from pathlib import Path

# Load .env file if it exists
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                # Set the value (overwriting empty env vars)
                os.environ[key] = value


# Import new modules (with graceful degradation if anthropic not installed)
try:
    from omniscient_bot import get_bot
    BOT_AVAILABLE = True
except (ImportError, ValueError) as e:
    BOT_AVAILABLE = False
    get_bot = None

try:
    from auditor import get_auditor
    AUDITOR_AVAILABLE = True
except (ImportError, ValueError):
    AUDITOR_AVAILABLE = False
    get_auditor = None

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
REVIEWED_PATH = os.path.join(REPO_ROOT, 'data', 'reviewed_financials.json')


def load_reviewed():
    try:
        with open(REVIEWED_PATH, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def save_reviewed(data):
    os.makedirs(os.path.dirname(REVIEWED_PATH), exist_ok=True)
    with open(REVIEWED_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def regenerate_dashboard(reviewed):
    """Merge approved reviewed values into dashboard_data.json and regenerate dashboard_data.js."""
    dash_path = os.path.join(REPO_ROOT, 'dashboard_data.json')
    js_path = os.path.join(REPO_ROOT, 'dashboard_data.js')

    with open(dash_path, encoding='utf-8') as f:
        dash_data = json.load(f)

    for key, entry in reviewed.items():
        if entry.get('status') != 'approved':
            continue
        # key format: "Company Name - YEAR"
        parts = key.rsplit(' - ', 1)
        if len(parts) != 2:
            continue
        company, year = parts[0], parts[1]
        if year not in dash_data.get('data', {}):
            continue
        for section in ('income_statement', 'balance_sheet', 'ratios'):
            if section not in entry:
                continue
            section_data = dash_data['data'][year].get(section, {})
            for field, value in entry[section].items():
                if field in section_data and company in section_data[field]:
                    try:
                        section_data[field][company] = float(value)
                    except (ValueError, TypeError):
                        pass

    with open(dash_path, 'w', encoding='utf-8') as f:
        json.dump(dash_data, f, separators=(',', ':'))

    with open(js_path, 'w', encoding='utf-8') as f:
        f.write('window.BMA_DASHBOARD_DATA = ')
        json.dump(dash_data, f, separators=(',', ':'))
        f.write(';')

    print(f"  Regenerated dashboard_data.json + dashboard_data.js")


def git_commit_push(key):
    try:
        subprocess.run(
            ['git', 'add', 'data/reviewed_financials.json', 'dashboard_data.json', 'dashboard_data.js'],
            cwd=REPO_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ['git', 'commit', '-m', f'Approve {key} financials'],
            cwd=REPO_ROOT, check=True, capture_output=True
        )
        subprocess.run(
            ['git', 'push', 'origin', 'main'],
            cwd=REPO_ROOT, check=True, capture_output=True
        )
        print(f"  Git push complete for: {key}")
        return True
    except subprocess.CalledProcessError as e:
        stderr = e.stderr.decode(errors='replace') if e.stderr else str(e)
        print(f"  Git error: {stderr}")
        return False


class BMAHandler(SimpleHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors_headers()
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/reviews':
            try:
                data = json.dumps(load_reviewed(), indent=2)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self._cors_headers()
                self.end_headers()
                self.wfile.write(data.encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        elif self.path == '/api/auditor/logs':
            self._handle_auditor_logs()
        else:
            super().do_GET()

    def do_POST(self):
        try:
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Bad request: {e}'}).encode())
            return

        # Route to appropriate handler
        if self.path == '/api/save':
            self._handle_save(body, approve=False)
        elif self.path == '/api/approve':
            self._handle_save(body, approve=True)
        elif self.path == '/api/bot/query':
            self._handle_bot_query(body)
        elif self.path == '/api/bot/analyze':
            self._handle_bot_analyze(body)
        elif self.path == '/api/bot/compare':
            self._handle_bot_compare(body)
        elif self.path == '/api/auditor/validate':
            self._handle_auditor_validate(body)
        elif self.path == '/api/fcr/upload':
            self._handle_fcr_upload(body)
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode())

    def _handle_save(self, body, approve=False):
        key = body.get('key', '')
        if not key:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing key'}).encode())
            return

        reviewed = load_reviewed()
        body['status'] = 'approved' if approve else body.get('status', 'draft')
        body['reviewed_at'] = datetime.now(timezone.utc).isoformat()
        reviewed[key] = body
        save_reviewed(reviewed)
        print(f"  Saved: {key} (status={body['status']})")

        result = {'ok': True, 'key': key, 'status': body['status']}

        if approve:
            try:
                regenerate_dashboard(reviewed)
            except Exception as e:
                print(f"  Warning: regenerate failed: {e}")
            result['pushed'] = git_commit_push(key)

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _handle_bot_query(self, body):
        """Handle bot query request."""
        if not BOT_AVAILABLE:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            result = {'error': 'Bot not available. Install: pip install anthropic'}
            self.wfile.write(json.dumps(result).encode())
            return

        company = body.get('company', '')
        question = body.get('question', '')
        year = body.get('year')

        if not company or not question:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing company or question'}).encode())
            return

        try:
            bot = get_bot()
            result = bot.query(company, question, year)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            print(f"  Bot query: {company} - audit_id={result.get('audit_id')}")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_bot_analyze(self, body):
        """Handle bot analyze request."""
        if not BOT_AVAILABLE:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Bot not available'}).encode())
            return

        company = body.get('company', '')
        year = body.get('year')
        metrics = body.get('metrics', ['financial', 'risk'])

        if not company:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing company'}).encode())
            return

        try:
            bot = get_bot()
            result = bot.analyze_company(company, year, metrics)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            print(f"  Bot analysis: {company} - audit_id={result.get('audit_id')}")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_bot_compare(self, body):
        """Handle bot compare request."""
        if not BOT_AVAILABLE:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Bot not available'}).encode())
            return

        companies = body.get('companies', [])
        year = body.get('year')

        if not companies or len(companies) < 2:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Need at least 2 companies'}).encode())
            return

        try:
            bot = get_bot()
            result = bot.compare_companies(companies, year)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            print(f"  Bot comparison: {len(companies)} companies - audit_id={result.get('audit_id')}")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_auditor_validate(self, body):
        """Handle auditor validation request."""
        if not AUDITOR_AVAILABLE:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Auditor not available'}).encode())
            return

        company = body.get('company', '')
        year = body.get('year')
        data = body.get('data', {})

        if not company or not year or not data:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Missing company, year, or data'}).encode())
            return

        try:
            auditor = get_auditor()
            result = auditor.validate(company, year, data)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
            print(f"  Auditor validation: {company} {year} - audit_id={result.get('audit_id')}")
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_auditor_logs(self):
        """Handle fetch audit logs request."""
        if not AUDITOR_AVAILABLE:
            self.send_response(503)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Auditor not available'}).encode())
            return

        try:
            auditor = get_auditor()
            logs = auditor.get_audit_log()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps(logs).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self._cors_headers()
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def _handle_fcr_upload(self, body):
        """Handle FCR document upload."""
        # Placeholder for FCR upload - would implement file handling
        audit_id = str(uuid.uuid4())[:12]

        company = body.get('company', '')
        year = body.get('year')

        result = {
            'status': 'success',
            'file_id': audit_id,
            'company': company,
            'year': year,
            'message': 'FCR upload endpoint ready (file handling not yet implemented)'
        }

        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self._cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")


if __name__ == '__main__':
    os.chdir(REPO_ROOT)
    port = int(os.getenv('SERVER_PORT', '5000'))
    server = HTTPServer(('localhost', port), BMAHandler)
    print(f"BMA Review Server running at http://localhost:{port}")
    print(f"  Dashboard:    http://localhost:{port}/dashboard.html")
    print(f"  Admin Review: http://localhost:{port}/admin_review.html")
    print("Press Ctrl+C to stop.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
