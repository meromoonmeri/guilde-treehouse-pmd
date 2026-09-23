"""Direct PNG/WebP/ZIP preview; no HTML dependency. Old raw URLs retained."""
from pathlib import Path
import sys,argparse,io,mimetypes,zipfile
from http.server import ThreadingHTTPServer
from urllib.parse import unquote,urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.spinda_decor_v1.serve import Handler as PreviousHandler
from source.dungeon_biomes_v1.archive import data,entries
from source.dungeon_biomes_v1.native_archive import native_source_archive
ARCHIVE={r['path'] for r in entries()}
PACK=R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip'
with zipfile.ZipFile(PACK) as z:PACKED=set(z.namelist())
class Handler(PreviousHandler):
 def send_head(self):
  path=unquote(urlsplit(self.path).path)
  if path=='/':self.path='/renders/dungeon_biomes_v1/apercus/DB1_collection.png'
  elif path=='/source/dungeon_biomes_v1/native_sources.zip':
   raw=native_source_archive().read_bytes();self.send_response(200);self.send_header('Content-Type','application/zip');self.send_header('Content-Length',str(len(raw)));self.end_headers();return io.BytesIO(raw)
  elif path.lstrip('/') in ARCHIVE:
   raw=data(R/path.lstrip('/'));self.send_response(200);self.send_header('Content-Type','image/webp');self.send_header('Content-Length',str(len(raw)));self.end_headers();return io.BytesIO(raw)
  elif path.startswith('/dungeon-pack/') and path.removeprefix('/dungeon-pack/') in PACKED:
   name=path.removeprefix('/dungeon-pack/')
   with zipfile.ZipFile(PACK) as z:raw=z.read(name)
   self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(raw)));self.end_headers();return io.BytesIO(raw)
  return super().send_head()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8011);a=p.parse_args();print(f'Direct dungeon PNG preview on 0.0.0.0:{a.port}',flush=True);ThreadingHTTPServer(('0.0.0.0',a.port),Handler).serve_forever()
