#!/usr/bin/env python3
import json, sqlite3, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

DB, HOST, PORT = sys.argv[1], sys.argv[2], int(sys.argv[3])

def query(sql, args=()):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(sql, args)]
    con.close()
    return rows

class H(BaseHTTPRequestHandler):
    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        p = parse_qs(u.query)
        if u.path == "/health":
            return self.send_json(200, {"status": "ok"})
        if u.path == "/badges":
            return self.send_json(200, query("SELECT id, holder, zone_access, active FROM badges"))
        if u.path == "/access":
            b, z = p.get("badge", [""])[0], p.get("zone", [""])[0]
            r = query("SELECT zone_access, active FROM badges WHERE id=?", (b,))
            ok = bool(r) and r[0]["active"] == 1 and z in r[0]["zone_access"].split(",")
            return self.send_json(200 if ok else 403, {"badge": b, "zone": z, "granted": ok})
        self.send_json(404, {"error": "not found"})

    def log_message(self, fmt, *a):
        sys.stderr.write("%s %s\n" % (self.client_address[0], fmt % a))

ThreadingHTTPServer((HOST, PORT), H).serve_forever()
