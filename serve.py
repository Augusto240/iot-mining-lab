#!/usr/bin/env python3
import http.server, socketserver, os

PORT = 8888
DIR = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
    print(f"Dashboard: http://localhost:{PORT}/dashboard.html")
    httpd.serve_forever()
