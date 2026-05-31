#!/usr/bin/env python3
"""
Deploy del fix responsive nav (38 HTML + subdirectorios).

Uso:
    SSH_ROOT_PASS="..." .venv/bin/python scripts/deploy_nav_fix.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import paramiko

MCP_DIR  = Path(__file__).resolve().parent.parent
PERU_DIR = MCP_DIR.parent

SSH_HOST    = "179.43.82.54"
SSH_PORT    = 22
SSH_USER    = "root"
SSH_PASS    = os.environ.get("SSH_ROOT_PASS", "")
REMOTE_BASE = "/var/www/html"

# 38 archivos HTML con el nav5-fix corregido
FILES = [
    "asesoramiento.html",
    "asesoramiento/informacion-tecnica.html",
    "asesoramiento/preguntas-frecuentes.html",
    "asesoramiento/seguridad.html",
    "asesoramiento/tips-de-seguridad.html",
    "blog.html",
    "blog/ciberseguridad-empresas-peru.html",
    "blog/cloud-colaboracion-productividad.html",
    "blog/colaboracion-equipos-hibridos.html",
    "blog/conectividad-empresarial-peru.html",
    "blog/monitoreo-red-empresarial.html",
    "blog/redundancia-continuidad-operativa.html",
    "blog/sdwan-transformacion-redes-empresariales.html",
    "canales-de-datos-peru.html",
    "cobertura.html",
    "contactanos.html",
    "encuesta-de-satisfaccion.html",
    "fibra-optica-empresas-peru.html",
    "gracias.html",
    "index.html",
    "informacion-tecnica.html",
    "internet-corporativo-peru.html",
    "internet-dedicado-peru.html",
    "normas-y-regulaciones.html",
    "normatividad-y-regulaciones/derechos-de-los-abonados.html",
    "normatividad-y-regulaciones/reglamentos-del-consumidor.html",
    "pqrs.html",
    "preguntas-frecuentes.html",
    "quienes-somos.html",
    "seguridad.html",
    "soluciones.html",
    "soluciones/cloud.html",
    "soluciones/collaboration.html",
    "soluciones/connection.html",
    "soluciones/security.html",
    "sumate-al-equipo.html",
    "tips-de-seguridad.html",
    "velocimetro.html",
]


def deploy():
    if not SSH_PASS:
        print("[Deploy] ERROR: Falta variable SSH_ROOT_PASS")
        print("  Uso: SSH_ROOT_PASS='...' .venv/bin/python scripts/deploy_nav_fix.py")
        sys.exit(1)

    print(f"[Deploy] {SSH_USER}@{SSH_HOST} — {len(FILES)} archivos HTML")

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
    ok = 0

    try:
        for rel in FILES:
            local_path  = PERU_DIR / rel
            remote_path = f"{REMOTE_BASE}/{rel}"

            if not local_path.exists():
                print(f"  [SKIP] {rel} — no encontrado localmente")
                continue

            # Crear directorio remoto si no existe
            remote_dir = remote_path.rsplit("/", 1)[0]
            try:
                sftp.stat(remote_dir)
            except FileNotFoundError:
                _, stdout, _ = client.exec_command(f"mkdir -p {remote_dir}")
                stdout.channel.recv_exit_status()

            size = local_path.stat().st_size
            try:
                sftp.put(str(local_path), remote_path)
                print(f"  ✓ {rel} ({size:,} bytes)")
                ok += 1
            except Exception as e:
                print(f"  ✗ {rel} → {e}")
                errors.append(rel)
    finally:
        sftp.close()
        client.close()

    print(f"\n[Deploy] {ok}/{len(FILES)} archivos OK")
    if errors:
        print(f"[Deploy] ERRORES: {errors}")
        sys.exit(1)
    print("[Deploy] Sitio: https://www.mcperu.pe")


if __name__ == "__main__":
    deploy()
