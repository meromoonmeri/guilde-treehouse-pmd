"""Direct PNG/WebP/ZIP delivery, including immutable Git-backed assets."""
from pathlib import Path
import sys,argparse,io,json,zipfile,mimetypes,subprocess,hashlib
from urllib.parse import unquote,urlsplit
from http.server import ThreadingHTTPServer
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from source.dungeon_biomes_v1.serve import Handler as PreviousHandler
from source.lisiere_pmd_v1.release import entries,materialize
RELEASE={r['path']:r for r in entries()}
RAW={r['path']:r for r in json.loads((Path(__file__).parent/'raws/archive.json').read_text())}
PACKNAME='LE1_lisiere_calques_et_effets.zip'
with zipfile.ZipFile(materialize(PACKNAME)) as z:PACKED=set(z.namelist())
class Handler(PreviousHandler):
 def send_bytes(self,raw,name):
  self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(raw)));self.end_headers();return io.BytesIO(raw)
 def send_head(self):
  path=unquote(urlsplit(self.path).path);rel=path.lstrip('/')
  if path=='/':self.path='/renders/lisiere_pmd_v1/LE1_lisiere.png'
  elif rel in RELEASE:return self.send_bytes(materialize(RELEASE[rel]['name']).read_bytes(),rel)
  elif rel in RAW:
   rec=RAW[rel];raw=subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R);assert hashlib.sha256(raw).hexdigest()==rec['sha256'];return self.send_bytes(raw,rel)
  elif path.startswith('/lisiere-pack/') and path.removeprefix('/lisiere-pack/') in PACKED:
   name=path.removeprefix('/lisiere-pack/')
   with zipfile.ZipFile(materialize(PACKNAME)) as z:raw=z.read(name)
   return self.send_bytes(raw,name)
  return super().send_head()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8012);a=p.parse_args();print(f'Forest-edge PNG preview on0.0.0.0:{a.port}',flush=True);ThreadingHTTPServer(('0.0.0.0',a.port),Handler).serve_forever()
