"""Read-only preview of the transformation deliverable, not a PMDO runtime."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]

class Gallery(SimpleHTTPRequestHandler):
    def do_GET(self):
        route = unquote(urlsplit(self.path).path)
        if route == '/':
            self.path = '/apercu_transformations_v1.html'
        elif route != '/apercu_transformations_v1.html' and not route.startswith('/exports/transformations_v1/'):
            self.send_error(404)
            return
        path = (ROOT / unquote(urlsplit(self.path).path).lstrip('/')).resolve()
        allowed = ROOT / 'exports/transformations_v1'
        if path != ROOT / 'apercu_transformations_v1.html' and (not path.is_relative_to(allowed) or not path.is_file()):
            self.send_error(404)
            return
        super().do_GET()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

if __name__ == '__main__':
    ThreadingHTTPServer(('0.0.0.0', 8000), Gallery).serve_forever()
