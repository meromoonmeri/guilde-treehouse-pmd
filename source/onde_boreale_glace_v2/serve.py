"""Galerie du climat boréal, serveur de prévisualisation uniquement."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[2]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_GET(self):
  if self.path=='/' or self.path.startswith('/?'):
   self.send_response(302);self.send_header('Location','/apercu_onde_boreale_glace_v2.html');self.end_headers()
  else:super().do_GET()
if __name__=='__main__':
 print('Onde boréale sur le ciel validé — http://0.0.0.0:8002',flush=True)
 ThreadingHTTPServer(('0.0.0.0',8002),Handler).serve_forever()
