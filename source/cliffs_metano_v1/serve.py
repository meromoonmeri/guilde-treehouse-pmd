"""Aperçu local : python source/cliffs_metano_v1/serve.py (port 8000)."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[2]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs): super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_GET(self):
  if self.path=='/' or self.path.startswith('/?'):
   self.send_response(302);self.send_header('Location','/apercu_cliffs_metano_v1.html');self.end_headers()
  else:super().do_GET()
if __name__=='__main__':
 print('Atelier des falaises Métano — http://0.0.0.0:8000',flush=True)
 ThreadingHTTPServer(('0.0.0.0',8000),Handler).serve_forever()
