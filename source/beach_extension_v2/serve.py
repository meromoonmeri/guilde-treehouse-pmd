"""Serve both beach lots under one origin; the preview opens the new extension."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from urllib.parse import urlsplit
import argparse
ROOT=Path(__file__).resolve().parents[2]/'renders'
class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def route_root(self):
        if urlsplit(self.path).path=='/':
            self.send_response(302);self.send_header('Location','/beach_extension_v2/index.html');self.end_headers();return True
        return False
    def do_GET(self):
        if not self.route_root():super().do_GET()
    def do_HEAD(self):
        if not self.route_root():super().do_HEAD()
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8002);args=parser.parse_args()
    server=ThreadingHTTPServer(('0.0.0.0',args.port),Handler)
    print(f'Beach extension preview listening on 0.0.0.0:{args.port}',flush=True);server.serve_forever()
