#!/usr/bin/env python3
"""
BMA Admin Review Server
Run: python approve.py
Serves at http://localhost:8080

Endpoints:
  GET  /api/reviews        -> returns data/reviewed_financials.json
  POST /api/save           -> merge body into reviewed_financials.json (status=draft)
  POST /api/approve        -> merge body (status=approved), regenerate dashboard, git push
  GET  *                   -> serve static files from repo root
"""
import json
import os
import subprocess
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime, timezone

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
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
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

        if self.path == '/api/save':
            self._handle_save(body, approve=False)
        elif self.path == '/api/approve':
            self._handle_save(body, approve=True)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not found')

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

    def _cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")


if __name__ == '__main__':
    os.chdir(REPO_ROOT)
    port = 8080
    server = HTTPServer(('localhost', port), BMAHandler)
    print(f"BMA Review Server running at http://localhost:{port}")
    print(f"  Dashboard:    http://localhost:{port}/dashboard.html")
    print(f"  Admin Review: http://localhost:{port}/admin_review.html")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
