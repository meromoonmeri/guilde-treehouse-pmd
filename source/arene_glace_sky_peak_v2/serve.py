from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
R=Path(__file__).resolve().parents[2]
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(R),**kwargs)
 def do_GET(self):
  if self.path=='/' or self.path.startswith('/?'):
   self.send_response(302);self.send_header('Location','/apercu_arene_glace_sky_peak_v2.html');self.end_headers()
  else:super().do_GET()
if __name__=='__main__':
 print('Arène du Croissant — aurore panoramique — port8004',flush=True)
 ThreadingHTTPServer(('0.0.0.0',8004),Handler).serve_forever()
