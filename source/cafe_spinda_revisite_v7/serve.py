"""Both current and historical workshop assets from one origin, including archived originals."""
from pathlib import Path
import sys,argparse,io
from urllib.parse import urlsplit,unquote
from http.server import ThreadingHTTPServer
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.cafe_spinda_revisite_v6.serve import Handler as PreviousHandler,restore_exports
from source.cafe_spinda_revisite_v7.archive import data,entries
ARCHIVE={r['path'] for r in entries()}
class Handler(PreviousHandler):
 def send_head(self):
  path=unquote(urlsplit(self.path).path)
  if path=='/':self.path='/apercu_cafe_spinda_revisite_v7.html'
  elif path.lstrip('/') in ARCHIVE and not (R/path.lstrip('/')).exists():
   raw=data(R/path.lstrip('/'));self.send_response(200);self.send_header('Content-Type','image/webp');self.send_header('Content-Length',str(len(raw)));self.end_headers();return io.BytesIO(raw)
  return super().send_head()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8007);a=p.parse_args();restore_exports(R/'renders/beach_network_v1')
 print(f'Spinda V7 workshop on 0.0.0.0:{a.port}',flush=True);ThreadingHTTPServer(('0.0.0.0',a.port),Handler).serve_forever()
