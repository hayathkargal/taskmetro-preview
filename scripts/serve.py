#!/usr/bin/env python3
"""Local preview at the same subdirectory used by GitHub Pages."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '/taskmetro-preview/'


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parts = urlsplit(self.path)
        if parts.path in ('/', PREFIX.rstrip('/')):
            self.send_response(302)
            self.send_header('Location', urlunsplit(('', '', PREFIX, parts.query, '')))
            self.end_headers()
            return
        if not parts.path.startswith(PREFIX):
            self.send_error(404)
            return
        self.path = urlunsplit(('', '', parts.path[len(PREFIX):], parts.query, ''))
        super().do_GET()

    def send_error(self, code, message=None, explain=None):
        if code != 404:
            return super().send_error(code, message, explain)
        body = (ROOT/'404.html').read_bytes()
        self.send_response(404)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        if self.command != 'HEAD':
            self.wfile.write(body)


if __name__ == '__main__':
    print('Preview: http://127.0.0.1:8765/taskmetro-preview/', flush=True)
    ThreadingHTTPServer(('127.0.0.1', 8765), Handler).serve_forever()
