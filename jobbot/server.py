from __future__ import annotations

import json
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from . import db
from .ingest import ingest_sample, ingest_targets
from .paths import DB_PATH, HOST, PORT, STATIC_DIR
from .review_queue import write_daily_queue


class Handler(BaseHTTPRequestHandler):
    server_version = "JobAssistant/0.2"

    def log_message(self, fmt, *args):
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, payload, status: int = 200):
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if not length:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        try:
            if path == "/":
                return self.serve_file(STATIC_DIR / "index.html", "text/html; charset=utf-8")
            if path.startswith("/static/"):
                rel = path.removeprefix("/static/")
                return self.serve_file(STATIC_DIR / rel)
            if path == "/api/jobs":
                return self.send_json(db.list_jobs(params))
            if path.startswith("/api/jobs/"):
                job_id = int(path.split("/")[3])
                job = db.get_job(job_id)
                return self.send_json(job or {"error": "not found"}, 200 if job else 404)
            if path == "/api/stats":
                return self.send_json(db.get_stats())
            self.send_error(404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/ingest":
                payload = self.read_json()
                result = ingest_targets() if payload.get("live", True) else ingest_sample()
                return self.send_json(result)
            if path == "/api/write-queue":
                return self.send_json(write_daily_queue())
            if path.startswith("/api/jobs/"):
                job_id = int(path.strip("/").split("/")[2])
                return self.send_json(db.update_job(job_id, self.read_json()))
            self.send_error(404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 500)

    def serve_file(self, path: Path, content_type: str | None = None):
        path = path.resolve()
        root = STATIC_DIR.parent.resolve()
        if not str(path).startswith(str(root)) or not path.exists() or not path.is_file():
            self.send_error(404)
            return
        suffix = path.suffix.lower()
        if content_type is None:
            content_type = {
                ".html": "text/html; charset=utf-8",
                ".css": "text/css; charset=utf-8",
                ".js": "text/javascript; charset=utf-8",
                ".json": "application/json; charset=utf-8",
            }.get(suffix, "application/octet-stream")
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def serve(host: str = HOST, port: int = PORT, db_path: Path = DB_PATH) -> None:
    db.init_db(db_path)
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"AI Job Application Assistant running at http://{host}:{port}")
    server.serve_forever()
