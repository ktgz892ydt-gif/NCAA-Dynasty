"""Serve a local preview; optionally expose one draft without changing the manifest."""
import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from season_io import ROOT, read
from validate_season import validate


def preview_manifest(season,root=ROOT):
    manifest=read(root/'data/seasons.json')
    if season:
        d=validate(season,root)
        manifest['seasons']=[s for s in manifest['seasons'] if s['id']!=str(season)]+[
            {'id':str(season),'label':f'{season} (preview)','published':True,'dataPath':f'data/seasons/{season}/season.json'}]
        manifest['defaultSeason']=str(season)
    return manifest


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--season');parser.add_argument('--port',type=int,default=8000);args=parser.parse_args()
    manifest=preview_manifest(args.season)
    class Handler(SimpleHTTPRequestHandler):
        def do_GET(self):
            if urlsplit(self.path).path=='/data/seasons.json':
                content=json.dumps(manifest).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Cache-Control','no-store');self.send_header('Content-Length',str(len(content)));self.end_headers();self.wfile.write(content)
            else:super().do_GET()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(ROOT)))
    print(f'Preview: http://127.0.0.1:{args.port}/ (local only; publication manifest unchanged)',flush=True)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
