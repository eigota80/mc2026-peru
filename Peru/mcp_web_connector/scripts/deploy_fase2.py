#!/usr/bin/env python3
"""
Deploy Fase 2 — sube archivos PHP, JS y CSS al servidor via SFTP.
Usa la misma infraestructura SSH del MCP. No modifica BD.

Uso: .venv/bin/python scripts/deploy_fase2.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import paramiko as _paramiko
if not hasattr(_paramiko, "DSSKey"):
    _paramiko.DSSKey = type("DSSKey", (_paramiko.PKey,), {
        "get_name": lambda self: "ssh-dss",
        "asbytes": lambda self: b"",
        "sign_ssh_data": lambda self, m, k=None: b"",
        "verify_ssh_sig": lambda self, m, msg: False,
        "get_bits": lambda self: 0,
    })

MCP_DIR = Path(__file__).resolve().parent.parent
PERU_DIR = MCP_DIR.parent
sys.path.insert(0, str(MCP_DIR))
from server import connect_ssh, settings  # noqa: E402

REMOTE_BASE = "/var/www/html"

# (local_path_relativo_a_PERU_DIR, remote_path)
FILES = [
    ("api/create-order.php",           f"{REMOTE_BASE}/api/create-order.php"),
    ("api/delete-order.php",           f"{REMOTE_BASE}/api/delete-order.php"),
    ("api/ordenes.php",                f"{REMOTE_BASE}/api/ordenes.php"),
    ("ordenes/ordenes-servicio.js",    f"{REMOTE_BASE}/ordenes/ordenes-servicio.js"),
    ("ordenes/ordenes-servicio.css",   f"{REMOTE_BASE}/ordenes/ordenes-servicio.css"),
    ("ordenes/index.html",             f"{REMOTE_BASE}/ordenes/index.html"),
    ("ordenes/dashboard.html",         f"{REMOTE_BASE}/ordenes/dashboard.html"),
    ("ordenes/ordenes.html",           f"{REMOTE_BASE}/ordenes/ordenes.html"),
    ("ordenes/cotizaciones.html",      f"{REMOTE_BASE}/ordenes/cotizaciones.html"),
    ("ordenes/Clientes.html",          f"{REMOTE_BASE}/ordenes/clientes.html"),
    ("ordenes/usuarios.html",          f"{REMOTE_BASE}/ordenes/usuarios.html"),
    ("ordenes/auditoria.html",         f"{REMOTE_BASE}/ordenes/auditoria.html"),
    ("ordenes/informes.html",          f"{REMOTE_BASE}/ordenes/informes.html"),
]


def deploy():
    cfg = settings()
    print(f"[Deploy] Host={cfg.ssh_host} user={cfg.ssh_user}")
    print(f"[Deploy] Archivos a desplegar: {len(FILES)}\n")

    client = connect_ssh()
    sftp = client.open_sftp()
    errors = []

    try:
        for local_rel, remote_path in FILES:
            local_path = PERU_DIR / local_rel
            if not local_path.exists():
                print(f"  [SKIP] {local_rel} — no encontrado localmente")
                continue

            size = local_path.stat().st_size
            try:
                sftp.put(str(local_path), remote_path)
                print(f"  ✓ {local_rel} → {remote_path} ({size:,} bytes)")
            except PermissionError as e:
                print(f"  ✗ {local_rel} → PERMISO DENEGADO: {e}")
                errors.append(local_rel)
            except FileNotFoundError as e:
                print(f"  ✗ {local_rel} → DIRECTORIO REMOTO NO EXISTE: {e}")
                errors.append(local_rel)
            except Exception as e:
                print(f"  ✗ {local_rel} → ERROR: {e}")
                errors.append(local_rel)

    finally:
        sftp.close()
        client.close()

    print()
    if errors:
        print(f"[Deploy] ERRORES en {len(errors)} archivo(s): {errors}")
        print("[Deploy] Si es problema de permisos, verificar que mcp-agent tenga acceso a /var/www/html/")
        sys.exit(1)
    else:
        print(f"[Deploy] ✓ {len(FILES)} archivos desplegados correctamente")
        print(f"[Deploy] URL produccion: https://www.mcperu.pe/ordenes/")


if __name__ == "__main__":
    deploy()
