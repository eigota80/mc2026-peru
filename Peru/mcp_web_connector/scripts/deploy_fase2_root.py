#!/usr/bin/env python3
"""
Deploy Fase 2 via root SSH (metodo temporal hasta configurar CI/CD).
El README documenta este mismo metodo como "Deploy rapido" activo.

Credenciales: SSH root con password — leidas del README de ordenes.
No hardcodea credenciales; las recibe por variable de entorno.

Uso:
    SSH_ROOT_PASS="..." .venv/bin/python scripts/deploy_fase2_root.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

MCP_DIR = Path(__file__).resolve().parent.parent
PERU_DIR = MCP_DIR.parent

SSH_HOST = "179.43.82.54"
SSH_PORT = 22
SSH_USER = "root"
SSH_PASS = os.environ.get("SSH_ROOT_PASS", "")
REMOTE_BASE = "/var/www/html"

FILES = [
    ("api/create-order.php",         f"{REMOTE_BASE}/api/create-order.php"),
    ("api/delete-order.php",         f"{REMOTE_BASE}/api/delete-order.php"),
    ("api/ordenes.php",              f"{REMOTE_BASE}/api/ordenes.php"),
    ("ordenes/ordenes-servicio.js",  f"{REMOTE_BASE}/ordenes/ordenes-servicio.js"),
    ("ordenes/ordenes-servicio.css", f"{REMOTE_BASE}/ordenes/ordenes-servicio.css"),
    ("ordenes/index.html",           f"{REMOTE_BASE}/ordenes/index.html"),
    ("ordenes/dashboard.html",       f"{REMOTE_BASE}/ordenes/dashboard.html"),
    ("ordenes/ordenes.html",         f"{REMOTE_BASE}/ordenes/ordenes.html"),
    ("ordenes/cotizaciones.html",    f"{REMOTE_BASE}/ordenes/cotizaciones.html"),
    ("ordenes/Clientes.html",        f"{REMOTE_BASE}/ordenes/clientes.html"),
    ("ordenes/usuarios.html",        f"{REMOTE_BASE}/ordenes/usuarios.html"),
    ("ordenes/auditoria.html",       f"{REMOTE_BASE}/ordenes/auditoria.html"),
    ("ordenes/informes.html",        f"{REMOTE_BASE}/ordenes/informes.html"),
]


def deploy():
    if not SSH_PASS:
        print("[Deploy] ERROR: Falta variable SSH_ROOT_PASS")
        print("  Uso: SSH_ROOT_PASS='...' .venv/bin/python scripts/deploy_fase2_root.py")
        sys.exit(1)

    print(f"[Deploy] {SSH_USER}@{SSH_HOST} — {len(FILES)} archivos")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.WarningPolicy())
    client.connect(
        hostname=SSH_HOST,
        port=SSH_PORT,
        username=SSH_USER,
        password=SSH_PASS,
        look_for_keys=False,
        allow_agent=False,
        timeout=15,
    )
    sftp = client.open_sftp()
    errors = []

    try:
        for local_rel, remote_path in FILES:
            local_path = PERU_DIR / local_rel
            if not local_path.exists():
                print(f"  [SKIP] {local_rel} — no encontrado")
                continue
            size = local_path.stat().st_size
            try:
                sftp.put(str(local_path), remote_path)
                print(f"  ✓ {local_rel} → {remote_path} ({size:,} bytes)")
            except Exception as e:
                print(f"  ✗ {local_rel} → {e}")
                errors.append(local_rel)
    finally:
        sftp.close()
        client.close()

    if errors:
        print(f"\n[Deploy] ERRORES: {errors}")
        sys.exit(1)

    print(f"\n[Deploy] ✓ {len(FILES)} archivos OK")
    print("[Deploy] URL: https://www.mcperu.pe/ordenes/")


if __name__ == "__main__":
    deploy()
