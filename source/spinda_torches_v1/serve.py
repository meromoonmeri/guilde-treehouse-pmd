"""One-origin workshop, including losslessly archived historical originals."""
from pathlib import Path
import sys,argparse,io,mimetypes,json,zipfile
from urllib.parse import urlsplit,unquote
from http.server import ThreadingHTTPServer
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.cafe_spinda_revisite_v8.serve import Handler as PreviousHandler
from source.spinda_torches_v1.archive import data,entries
ARCHIVE={r['path'] for r in entries()}
O=R/'renders/spinda_torches_v1'
PACKED=set(json.loads((O/'manifest.json').read_text()).get('zip_backed_assets',[]))
class Handler(PreviousHandler):
 def send_head(self):
  path=unquote(urlsplit(self.path).path)
  if path=='/':self.path='/apercu_spinda_torches.html'
  elif path.lstrip('/') in ARCHIVE and not (R/path.lstrip('/')).exists():
   raw=data(R/path.lstrip('/'));self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(path)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(raw)));self.end_headers();return io.BytesIO(raw)
  elif path.startswith('/renders/spinda_torches_v1/') and path.removeprefix('/renders/spinda_torches_v1/') in PACKED:
   name=path.removeprefix('/renders/spinda_torches_v1/')
   with zipfile.ZipFile(O/'Spinda_torches_8angles_animees.zip') as z:raw=z.read(name)
   self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(raw)));self.end_headers();return io.BytesIO(raw)
  return super().send_head()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8009);a=p.parse_args()
 print(f'Spinda eight-angle animated wall torch workshop on 0.0.0.0:{a.port}',flush=True);ThreadingHTTPServer(('0.0.0.0',a.port),Handler).serve_forever()
