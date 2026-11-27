#!/usr/bin/env python3
import json, os, ssl, sqlite3, sys, time, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB = os.environ["DB"]
URL = os.environ["DCS_URL"]
VERIFY = os.environ.get("DCS_VERIFY", "true").lower()
HOST = os.environ.get("LISTEN", "0.0.0.0")
PORT = int(os.environ.get("PORT", "8080"))

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE IF NOT EXISTS manifestes (id TEXT PRIMARY KEY, nom TEXT, vol TEXT, passeport TEXT, statut TEXT, maj INTEGER)")
    return c

def sync():
    ctx = ssl.create_default_context()
    if VERIFY == "false":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(URL, timeout=5, context=ctx) as r:
        data = json.load(r)
    c = db()
    for p in data:
        c.execute("INSERT OR REPLACE INTO manifestes VALUES (?,?,?,?,?,?)",
                  (str(p["id"]), p.get("nom"), p.get("vol"), p.get("passeport"), p.get("statut"), int(time.time())))
    c.commit()
    c.close()
    return len(data)

def rows():
    c = db()
    r = [dict(x) for x in c.execute("SELECT * FROM manifestes ORDER BY vol, nom")]
    c.close()
    return r

class H(BaseHTTPRequestHandler):
    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/health":
            return self.send_json(200, {"status": "ok"})
        if path == "/manifestes":
            try:
                sync()
                src, err = "dcs", None
            except Exception as e:
                src, err = "cache", str(e)
            return self.send_json(200, {"source": src, "erreur": err, "manifestes": rows()})
        self.send_json(404, {"error": "not found"})

    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.client_address[0], fmt % a))

ThreadingHTTPServer((HOST, PORT), H).serve_forever()
