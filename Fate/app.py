# -*- coding: utf-8 -*-
"""手机择日页。在项目目录运行：python app.py"""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import fate_api

ROOT = Path(__file__).resolve().parent / "web"
HOST = "0.0.0.0"
PORT = 8765
TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".webmanifest": "application/manifest+json; charset=utf-8",
    ".png": "image/png",
}


class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))

    def _send(self, code, body, content_type):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        rel = self.path.split("?", 1)[0]
        if rel == "/":
            rel = "/index.html"
        target = (ROOT / rel.lstrip("/")).resolve()
        if not str(target).startswith(str(ROOT.resolve())) or not target.is_file():
            self._send(404, "找不到页面", "text/plain; charset=utf-8")
            return
        self._send(200, target.read_bytes(), TYPES.get(target.suffix, "application/octet-stream"))

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/api/calc":
            self._send(404, json.dumps({"error": "没有这个接口"}, ensure_ascii=False), "application/json; charset=utf-8")
            return
        length = int(self.headers.get("Content-Length", "0") or 0)
        try:
            raw = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            payload = fate_api.build_query(raw)
        except ValueError as exc:
            self._send(400, json.dumps({"error": str(exc)}, ensure_ascii=False), "application/json; charset=utf-8")
            return
        except Exception:
            self._send(500, json.dumps({"error": "排盘失败，请检查填写的日期"}, ensure_ascii=False), "application/json; charset=utf-8")
            return
        self._send(200, json.dumps(payload, ensure_ascii=False), "application/json; charset=utf-8")


def main():
    server = ThreadingHTTPServer((HOST, PORT), AppHandler)
    print("择日已打开：http://127.0.0.1:%s" % PORT)
    print("手机请用同一局域网地址访问此端口")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    main()
