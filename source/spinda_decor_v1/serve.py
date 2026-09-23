"""Direct PNG preview, no HTML dependency; preserve historical archive URLs."""
from pathlib import Path
import sys,argparse,io
from http.server import ThreadingHTTPServer
from urllib.parse import unquote,urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.spinda_torches_v1.serve import Handler as PreviousHandler
from source.spinda_decor_v1.archive import data,entries
ARCHIVE={r['path'] for r in entries()}
class Handler(PreviousHandler):
 def send_head(self):
  path=unquote(urlsplit(self.path).path)
  if path=='/':self.path='/renders/spinda_decor_v1/apercus/SpindaDecor_cafe_demonstration.png'
  elif path.lstrip('/') in ARCHIVE:
   b=data(R/path.lstrip('/'));self.send_response(200);self.send_header('Content-Type','image/webp');self.send_header('Content-Length',str(len(b)));self.end_headers();return io.BytesIO(b)
  return super().send_head()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8010);a=p.parse_args();print(f'Spinda direct PNG preview on 0.0.0.0:{a.port}',flush=True);ThreadingHTTPServer(('0.0.0.0',a.port),Handler).serve_forever()
