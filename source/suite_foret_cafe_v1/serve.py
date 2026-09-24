"""Allowlisted direct PNG/WebP/ZIP preview; immutable Git-backed assets."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlsplit,unquote
import argparse,mimetypes,zipfile
from storage import records,materialize
class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  path=unquote(urlsplit(self.path).path);aliases={'/':'LF1_duo.png','/finale':'LF1_finale.png','/animation':'LF1_finale_animee.webp','/mobilier':'FC1_mobilier.png','/cafe':'FC1_cafe_echelle1x.png'};name=aliases.get(path,path.lstrip('/'))
  try:
   if name in {r['name'] for r in records()}:data=materialize(name).read_bytes()
   else:
    packs={'/foret-pack/':'LF1_finale_calques.zip','/cafe-pack/':'FC1_mobilier_taille_import.zip'};prefix=next((p for p in packs if path.startswith(p)),None)
    if not prefix:raise KeyError(path)
    name=path[len(prefix):]
    with zipfile.ZipFile(materialize(packs[prefix])) as z:data=z.read(name)
   self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(data)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(data)
  except (KeyError,StopIteration):self.send_error(404)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--port',type=int,default=8013);a=p.parse_args();print(f'Direct PNG/WebP preview on 0.0.0.0:{a.port}',flush=True);ThreadingHTTPServer(('0.0.0.0',a.port),Handler).serve_forever()
