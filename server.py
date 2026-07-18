#!/usr/bin/env python3
"""动画精选平台 - 本地代理服务器"""
import http.server
import urllib.request
import urllib.parse
import json
import os
import sys

PORT = 8000
DIR = os.path.dirname(os.path.abspath(__file__))

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split('?')[0]  # path without query
        query = self.path  # full path with query

        # B站 API 代理
        if path == '/api/bilibili':
            params = urllib.parse.parse_qs(urllib.parse.urlparse(query).query)
            bvid = params.get('bvid', [''])[0]
            if not bvid:
                self._send_json(400, {'code': -1, 'message': 'Missing bvid'})
                return
            url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid}'
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36',
                    'Referer': 'https://www.bilibili.com/',
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                self._send_json(200, data)
            except Exception as e:
                self._send_json(500, {'code': -1, 'message': str(e)})
            return

        # YouTube oEmbed 代理
        if path == '/api/youtube':
            params = urllib.parse.parse_qs(urllib.parse.urlparse(query).query)
            vid = params.get('vid', [''])[0]
            if not vid:
                self._send_json(400, {'error': 'Missing vid'})
                return
            url = f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json'
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0.0.0 Safari/537.36',
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                self._send_json(200, data)
            except Exception as e:
                self._send_json(500, {'error': str(e)})
            return

        # 静态文件服务
        self._serve_static()

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache')
        self.end_headers()
        if isinstance(data, bytes):
            self.wfile.write(data)
        else:
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def _serve_static(self):
        path = self.path.split('?')[0]
        if path == '/':
            path = '/动画精选平台.html'
        filepath = os.path.join(DIR, path.lstrip('/'))
        if not os.path.exists(filepath):
            self.send_error(404, 'File not found')
            return
        ext = os.path.splitext(filepath)[1]
        content_types = {
            '.html': 'text/html; charset=utf-8',
            '.css': 'text/css; charset=utf-8',
            '.js': 'application/javascript; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.svg': 'image/svg+xml',
        }
        ctype = content_types.get(ext, 'application/octet-stream')
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_error(500, str(e))

    def log_message(self, fmt, *args):
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

if __name__ == '__main__':
    os.chdir(DIR)
    server = http.server.HTTPServer(('0.0.0.0', PORT), ProxyHandler)
    print(f'🚀 动画平台服务器：http://localhost:{PORT}')
    print(f'🔧 B站代理：http://localhost:{PORT}/api/bilibili?bvid=BVxxx')
    print('按 Ctrl+C 停止')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止')
        server.server_close()
