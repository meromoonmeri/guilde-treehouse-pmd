"""Direct-preview server: PNG and WebP URLs, no HTML required.

    .venv/bin/python source/canon_dtef_v1/serve.py --port 8013

The repository root is served so `/renders/canon_dtef_v1/apercus/...png` URLs work
as-is. `index.html` only lists those URLs; opening a PNG directly never needs it.
"""
from __future__ import annotations

import argparse
import functools
import html
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders/canon_dtef_v1'


class Handler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map,
                      '.webp': 'image/webp', '.png': 'image/png', '.ora': 'image/x-openraster',
                      '.rsground': 'application/json'}

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()


def index():
    files = sorted(OUT.rglob('*'))
    rows = []
    for p in files:
        if p.is_file() and p.suffix.lower() in {'.png', '.webp', '.jpg'}:
            rel = p.relative_to(ROOT).as_posix()
            size = p.stat().st_size
            img = f'<img src="/{rel}" alt="" style="max-width:100%;image-rendering:pixelated">' \
                if p.suffix.lower() == '.png' and 'apercus' in rel else ''
            rows.append(f'<li><a href="/{rel}">{rel}</a> · {size // 1024} Ko {img}</li>')
    return ('<!doctype html><meta charset="utf-8"><title>CANON1</title>'
            '<style>body{background:#12121a;color:#e8e8ee;font:14px system-ui;max-width:1100px;margin:24px auto;}'
            'img{display:block;margin:8px 0;border:1px solid #333}li{margin:6px 0}</style>'
            '<h1>CANON1 — cartes en cellules natives</h1><p>Direct PNG/WebP, aucune dependence HTML.</p><ul>'
            + '\n'.join(rows) + '</ul>')


class Quiet(Handler):
    def do_GET(self):  # noqa: N802
        if self.path in ('/', '/index.html'):
            body = index().encode()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8013)
    args = parser.parse_args()
    handler = functools.partial(Quiet, directory=str(ROOT))
    server = ThreadingHTTPServer(('0.0.0.0', args.port), handler)
    print(f'CAS: CANON1 sur http://0.0.0.0:{args.port} (racine = depot)')
    server.serve_forever()


if __name__ == '__main__':
    main()
