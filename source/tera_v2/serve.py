"""Read-only gallery server; no access to arbitrary repository files."""
from pathlib import Path
from urllib.parse import unquote,urlsplit
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[2]
PAGE=ROOT/'apercu_tera_v2.html'
ALLOWED=[ROOT/p for p in ['exports/tera_v2','exports/pokemon_custom/tirtouga_v5/review/gifs','exports/pokemon_custom/tirtouga_portraits_v4/portraits_individual','source/pokemon_custom/next_species/references']]
class Handler(SimpleHTTPRequestHandler):
    def allowed(self):
        route=unquote(urlsplit(self.path).path)
        if route=='/':self.path='/apercu_tera_v2.html';route=self.path
        path=(ROOT/route.lstrip('/')).resolve()
        return path.is_file() and (path==PAGE or any(path.is_relative_to(p) for p in ALLOWED))
    def do_GET(self):
        if self.allowed():super().do_GET()
        else:self.send_error(404)
    def do_HEAD(self):
        if self.allowed():super().do_HEAD()
        else:self.send_error(404)
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
if __name__=='__main__':ThreadingHTTPServer(('0.0.0.0',8001),Handler).serve_forever()
