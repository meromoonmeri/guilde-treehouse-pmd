"""Aperçu de la collection glacée, port8001, accepte le proxy Arena."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[2]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_GET(self):
  if self.path=='/' or self.path.startswith('/?'):
   self.send_response(302);self.send_header('Location','/apercu_entrees_glace_v1.html');self.end_headers()
  else:super().do_GET()
if __name__=='__main__':
 print('Entrées de grottes glacées — http://0.0.0.0:8001',flush=True)
 ThreadingHTTPServer(('0.0.0.0',8001),Handler).serve_forever()
