"""Python preview backend for the Ordenes de Servicio system.

This server intentionally keeps the current localStorage flow intact while
exposing small API endpoints and serving the static app from the Peru web root.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

try:
	from .db import get_mariadb_config
except ImportError:
	from db import get_mariadb_config


MODULE_ROOT = Path(__file__).resolve().parents[1]
WEB_ROOT = MODULE_ROOT.parent
SCHEMA_PATH = MODULE_ROOT / "backend" / "mariadb_schema.sql"
LOGIN_PATH = "/Ordenes%20de%20servicios/ordenes-servicio.html"

MODULES = [
	{"id": "dashboard", "label": "Dashboard", "permission": None},
	{"id": "clientes", "label": "Clientes", "permission": "create_clients"},
	{"id": "ordenes", "label": "Ordenes", "permission": "create_orders"},
	{"id": "cotizaciones", "label": "Cotizaciones", "permission": "create_orders"},
	{"id": "usuarios", "label": "Usuarios", "permission": "manage_users"},
	{"id": "auditoria", "label": "Auditorias", "permission": "manage_users"},
]

LOCAL_STORAGE_KEYS = [
	"mcperu_os_users",
	"mcperu_os_clients",
	"mcperu_os_orders",
	"mcperu_os_cotizaciones",
	"mcperu_os_audit",
	"mcperu_os_session",
	"mcperu_service_order_next_number",
	"mcperu_os_cot_next_number",
	"mcperu_service_order_draft",
	"mcperu_os_users_seed_version",
	"mcperu_os_data_version",
]


class PreviewHandler(BaseHTTPRequestHandler):
	server_version = "MCPeruOrdenesPreview/1.0"

	def end_headers(self) -> None:
		self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1")
		self.send_header("X-Content-Type-Options", "nosniff")
		super().end_headers()

	def do_GET(self) -> None:
		path = urlparse(self.path).path
		if path == "/":
			self.send_response(HTTPStatus.FOUND)
			self.send_header("Location", LOGIN_PATH)
			self.end_headers()
			return
		if path == "/health":
			self.send_json({
				"status": "ok",
				"frontend_storage": "localStorage",
				"database": "mariadb-ready" if get_mariadb_config().is_configured else "mariadb-not-configured",
			})
			return
		if path == "/api/modules":
			self.send_json({"modules": MODULES})
			return
		if path == "/api/storage-map":
			self.send_json({"storage": "localStorage", "keys": LOCAL_STORAGE_KEYS})
			return
		if path == "/api/mariadb/schema":
			self.send_text(SCHEMA_PATH.read_text(encoding="utf-8"), "text/plain; charset=utf-8")
			return
		self.serve_static(path)

	def send_json(self, payload: dict) -> None:
		body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
		self.send_response(HTTPStatus.OK)
		self.send_header("Content-Type", "application/json; charset=utf-8")
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def send_text(self, text: str, content_type: str) -> None:
		body = text.encode("utf-8")
		self.send_response(HTTPStatus.OK)
		self.send_header("Content-Type", content_type)
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def serve_static(self, path: str) -> None:
		relative = unquote(path).lstrip("/")
		target = (WEB_ROOT / relative).resolve()
		if not self.is_safe_path(target):
			self.send_error(HTTPStatus.FORBIDDEN)
			return
		if target.is_dir():
			target = target / "index.html"
		if not target.exists() or not target.is_file():
			self.send_error(HTTPStatus.NOT_FOUND)
			return
		content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
		body = target.read_bytes()
		self.send_response(HTTPStatus.OK)
		self.send_header("Content-Type", content_type)
		self.send_header("Content-Length", str(len(body)))
		self.end_headers()
		self.wfile.write(body)

	def is_safe_path(self, target: Path) -> bool:
		return target == WEB_ROOT or WEB_ROOT in target.parents

	def log_message(self, format: str, *args: object) -> None:
		print("%s - %s" % (self.address_string(), format % args))


def main() -> None:
	parser = argparse.ArgumentParser(description="Run the Ordenes de Servicio preview backend.")
	parser.add_argument("--host", default="127.0.0.1")
	parser.add_argument("--port", default=8001, type=int)
	args = parser.parse_args()

	server = ThreadingHTTPServer((args.host, args.port), PreviewHandler)
	print(f"Preview backend running at http://{args.host}:{args.port}{LOGIN_PATH}")
	server.serve_forever()


if __name__ == "__main__":
	main()
