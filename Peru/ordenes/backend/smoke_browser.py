"""Headless browser smoke test for the local preview.

Requires Google Chrome. It uses the Chrome DevTools Protocol with only Python
standard-library modules, so no npm/pip dependencies are needed.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse


PREVIEW_URL = "http://127.0.0.1:8001/Ordenes%20de%20servicios/ordenes-servicio.html"
DEBUG_PORT = 9223


class CDPClient:
	def __init__(self, websocket_url: str) -> None:
		parsed = urlparse(websocket_url)
		self.host = parsed.hostname or "127.0.0.1"
		self.port = parsed.port or DEBUG_PORT
		self.path = parsed.path + (f"?{parsed.query}" if parsed.query else "")
		self.sock = socket.create_connection((self.host, self.port), timeout=5)
		self.next_id = 1
		self._handshake()

	def _handshake(self) -> None:
		key = base64.b64encode(os.urandom(16)).decode("ascii")
		request = (
			f"GET {self.path} HTTP/1.1\r\n"
			f"Host: {self.host}:{self.port}\r\n"
			f"Origin: http://127.0.0.1:{DEBUG_PORT}\r\n"
			"Upgrade: websocket\r\n"
			"Connection: Upgrade\r\n"
			f"Sec-WebSocket-Key: {key}\r\n"
			"Sec-WebSocket-Version: 13\r\n\r\n"
		)
		self.sock.sendall(request.encode("ascii"))
		response = self.sock.recv(4096).decode("iso-8859-1")
		if "101 " not in response and "101 Switching Protocols" not in response:
			raise RuntimeError(f"Chrome DevTools websocket handshake failed: {response[:240]!r}")

	def send(self, method: str, params: dict | None = None) -> dict:
		message_id = self.next_id
		self.next_id += 1
		payload = json.dumps({"id": message_id, "method": method, "params": params or {}}).encode("utf-8")
		self.sock.sendall(self._encode_frame(payload))
		while True:
			message = json.loads(self._read_frame().decode("utf-8"))
			if message.get("id") == message_id:
				if "error" in message:
					raise RuntimeError(message["error"])
				return message

	def evaluate(self, expression: str) -> object:
		response = self.send("Runtime.evaluate", {
			"expression": expression,
			"awaitPromise": True,
			"returnByValue": True,
		})
		result = response["result"]["result"]
		return result.get("value")

	def close(self) -> None:
		self.sock.close()

	def _encode_frame(self, payload: bytes) -> bytes:
		header = bytearray([0x81])
		length = len(payload)
		if length < 126:
			header.append(0x80 | length)
		elif length < 65536:
			header.extend([0x80 | 126])
			header.extend(struct.pack("!H", length))
		else:
			header.extend([0x80 | 127])
			header.extend(struct.pack("!Q", length))
		mask = os.urandom(4)
		masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
		return bytes(header) + mask + masked

	def _read_frame(self) -> bytes:
		first = self.sock.recv(2)
		if len(first) < 2:
			raise RuntimeError("Unexpected websocket close.")
		opcode = first[0] & 0x0F
		length = first[1] & 0x7F
		if length == 126:
			length = struct.unpack("!H", self._read_exact(2))[0]
		elif length == 127:
			length = struct.unpack("!Q", self._read_exact(8))[0]
		mask = self._read_exact(4) if first[1] & 0x80 else None
		payload = self._read_exact(length)
		if mask:
			payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
		if opcode == 0x9:
			return self._read_frame()
		if opcode == 0x8:
			raise RuntimeError("Websocket closed by Chrome.")
		return payload

	def _read_exact(self, length: int) -> bytes:
		chunks = bytearray()
		while len(chunks) < length:
			chunk = self.sock.recv(length - len(chunks))
			if not chunk:
				raise RuntimeError("Unexpected websocket close.")
			chunks.extend(chunk)
		return bytes(chunks)


def find_chrome() -> str:
	candidates = [
		"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
		"/Applications/Chromium.app/Contents/MacOS/Chromium",
	]
	for candidate in candidates:
		if Path(candidate).exists():
			return candidate
	chrome = shutil.which("google-chrome") or shutil.which("chromium")
	if chrome:
		return chrome
	raise RuntimeError("Google Chrome/Chromium not found.")


def wait_for_debugger() -> str:
	deadline = time.time() + 10
	while time.time() < deadline:
		try:
			with urllib.request.urlopen(f"http://127.0.0.1:{DEBUG_PORT}/json/list", timeout=1) as response:
				tabs = json.loads(response.read().decode("utf-8"))
				if tabs:
					return tabs[0]["webSocketDebuggerUrl"]
		except Exception:
			time.sleep(0.2)
	raise RuntimeError("Chrome DevTools endpoint did not start.")


def wait_until(client: CDPClient, expression: str, timeout: int = 8) -> object:
	deadline = time.time() + timeout
	last = None
	while time.time() < deadline:
		last = client.evaluate(expression)
		if last:
			return last
		time.sleep(0.2)
	raise RuntimeError(f"Timed out waiting for: {expression}. Last value: {last!r}")


def run() -> dict:
	profile = Path(tempfile.gettempdir()) / "mcperu_chrome_smoke_profile"
	profile.mkdir(parents=True, exist_ok=True)
	chrome = subprocess.Popen([
		find_chrome(),
		"--headless=new",
		"--disable-gpu",
		"--no-first-run",
		"--no-default-browser-check",
		"--remote-allow-origins=*",
		f"--remote-debugging-port={DEBUG_PORT}",
		f"--user-data-dir={profile}",
		PREVIEW_URL,
	], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	client = None
	try:
		client = CDPClient(wait_for_debugger())
		wait_until(client, "document.readyState === 'complete'")
		client.evaluate("localStorage.clear(); location.href = '%s';" % PREVIEW_URL)
		wait_until(client, "document.getElementById('loginForm') !== null && localStorage.getItem('mcperu_os_users') !== null")
		time.sleep(0.5)
		client.evaluate("""
			document.getElementById('loginEmail').value = 'eider.gonzalez@mcperu.pe';
			document.getElementById('loginPassword').value = 'GonzalezEider2024+';
			document.getElementById('loginForm').requestSubmit();
		""")
		wait_until(client, "location.href.includes('index.html') && document.getElementById('appView') && !document.getElementById('appView').hidden && document.getElementById('sessionName').textContent.length > 0")
		admin_home = client.evaluate("document.getElementById('viewTitle').textContent")
		admin_users_visible = client.evaluate("!document.querySelector('[data-home-target=\"usuarios\"]').hidden")
		admin_navigation = []
		for target in ["dashboard", "clientes", "ordenes", "cotizaciones", "usuarios", "auditoria"]:
			client.evaluate("document.querySelector('[data-view=\"home\"]').click()")
			wait_until(client, "document.getElementById('homeView') && !document.getElementById('homeView').hidden")
			client.evaluate(f"document.querySelector('[data-home-target=\"{target}\"]').click()")
			wait_until(client, f"document.getElementById('{target}View') && !document.getElementById('{target}View').hidden")
			admin_navigation.append(target)
		client.evaluate("document.getElementById('logoutBtn').click()")
		wait_until(client, "location.href.includes('ordenes-servicio.html') && document.getElementById('loginForm') !== null && localStorage.getItem('mcperu_os_users') !== null")
		time.sleep(0.5)
		client.evaluate("""
			document.getElementById('loginEmail').value = 'renato.mejia@mcperu.pe';
			document.getElementById('loginPassword').value = 'MejiaRenato2023+';
			document.getElementById('loginForm').requestSubmit();
		""")
		wait_until(client, "location.href.includes('index.html') && document.getElementById('appView') && !document.getElementById('appView').hidden && document.getElementById('sessionName').textContent.length > 0")
		comercial_home = client.evaluate("document.getElementById('viewTitle').textContent")
		comercial_users_hidden = client.evaluate("document.querySelector('[data-home-target=\"usuarios\"]').hidden")
		comercial_audit_hidden = client.evaluate("document.querySelector('[data-home-target=\"auditoria\"]').hidden")
		return {
			"admin_login_home": admin_home,
			"admin_users_visible": admin_users_visible,
			"admin_home_navigation": admin_navigation,
			"comercial_login_home": comercial_home,
			"comercial_users_hidden": comercial_users_hidden,
			"comercial_auditorias_hidden": comercial_audit_hidden,
		}
	finally:
		if client:
			client.close()
		chrome.terminate()
		chrome.wait(timeout=5)


if __name__ == "__main__":
	print(json.dumps(run(), indent=2, ensure_ascii=True))
