#!/usr/bin/env python3
"""
Simple HTTP server to serve the insurance dashboard
"""
import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

# Change to the directory containing the dashboard files
dashboard_dir = Path(__file__).parent

os.chdir(dashboard_dir)

PORT = 8001

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add headers to prevent caching
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

try:
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print("=" * 70)
        print("INSURANCE DASHBOARD SERVER")
        print("=" * 70)
        print(f"\n[OK] Server started on {url}\n")
        print("Opening dashboard in your browser...\n")
        print("Press Ctrl+C to stop the server\n")

        # Open browser
        webbrowser.open(url)

        # Serve
        httpd.serve_forever()

except KeyboardInterrupt:
    print("\n\n[OK] Server stopped")
except OSError as e:
    if e.errno == 48:  # Port already in use
        print(f"\nError: Port {PORT} is already in use")
        print(f"Try running: python -m http.server {PORT+1}")
    else:
        raise
