"""Preview both workshops from one origin; restore pre-existing archived Beach exports."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,unquote
import sys,argparse,json,io
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.beach_network_v1.restore_exports import restore_exports
from source.cafe_spinda_reseau_v4.archive_studies import read_bytes
from source.cafe_spinda_revisite_v7.archive import data as raw_bytes,entries as raw_entries
from source.casino_network_v1.archive import data as casino_raw,entries as casino_entries
CASINO_ARCHIVE={r['path'] for r in casino_entries()}
RAW_ARCHIVE={r['path'] for r in raw_entries()}
ARCHIVED={r['git_path'] for r in json.loads((R/'renders/cafe_spinda_reseau_v4/bruts/archived_studies.json').read_text())}
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(R),**kwargs)
 def send_head(self):
  path=unquote(urlsplit(self.path).path)
  if any(s.startswith('.') for s in path.split('/') if s):self.send_error(404);return None
  if path.lstrip('/') in CASINO_ARCHIVE and not (R/path.lstrip('/')).exists():
   data=casino_raw(R/path.lstrip('/'));self.send_response(200);self.send_header('Content-Type','image/webp');self.send_header('Content-Length',str(len(data)));self.end_headers();return io.BytesIO(data)
  if path.lstrip('/') in ARCHIVED and not (R/path.lstrip('/')).exists():
   data=read_bytes(R/path.lstrip('/'));self.send_response(200);self.send_header('Content-Type','image/webp');self.send_header('Content-Length',str(len(data)));self.end_headers();return io.BytesIO(data)
  if path.lstrip('/') in RAW_ARCHIVE and not (R/path.lstrip('/')).exists():
   data=raw_bytes(R/path.lstrip('/'));self.send_response(200);self.send_header('Content-Type','image/webp');self.send_header('Content-Length',str(len(data)));self.end_headers();return io.BytesIO(data)
  if path=='/':self.path='/apercu_cafe_spinda_revisite_v6.html'
  return super().send_head()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8006);a=p.parse_args()
 print('Restored Beach exports:',restore_exports(R/'renders/beach_network_v1'),flush=True)
 print(f'Spinda and Beach workshops on 0.0.0.0:{a.port}',flush=True);ThreadingHTTPServer(('0.0.0.0',a.port),Handler).serve_forever()
