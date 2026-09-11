"""Serveur de prévisualisation en lecture seule, sans exposer les fichiers internes."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit, unquote
import argparse

ROOT = Path(__file__).resolve().parents[1]
ENTRY = 'apercu_falaise.html'
ALLOWED = {'apercu_falaise.html', 'apercu_reve.html', 'apercu_pmd.html', 'falaise', 'sharpedo', 'reve', 'previews'}


class Preview(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        requested = unquote(urlsplit(self.path).path)
        if requested == '/':
            self.path = '/'+ENTRY
            requested = self.path
        try:
            relative = (ROOT / requested.lstrip('/')).resolve().relative_to(ROOT)
        except ValueError:
            self.send_error(403)
            return None
        if not relative.parts or relative.parts[0] not in ALLOWED:
            self.send_error(404)
            return None
        return super().send_head()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--page', choices=['apercu_falaise.html','apercu_reve.html'], default='apercu_falaise.html')
    args = parser.parse_args()
    ENTRY = args.page
    ThreadingHTTPServer(('0.0.0.0', args.port), Preview).serve_forever()
