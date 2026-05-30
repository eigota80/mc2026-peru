#!/usr/bin/env python3
"""
Ejecuta la migración 20260529_os_consecutivo_global.sql en bdmcperu.
Usa las mismas credenciales SSH/BD que el servidor MCP.
Solo ejecutar migraciones controladas — no usar para consultas ad-hoc.

Uso:
    .venv/bin/python scripts/run_migration.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Monkey-patch DSSKey antes de importar server (compatibilidad paramiko 5.x)
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
MIGRATION_FILE = MCP_DIR.parent / "database" / "migrations" / "20260529_os_consecutivo_global.sql"

sys.path.insert(0, str(MCP_DIR))
from server import db_connection, settings  # noqa: E402


def run():
    cfg = settings()
    print(f"[Migration] DB={cfg.db_name} @ {cfg.ssh_host} user={cfg.db_user}")

    sql_raw = MIGRATION_FILE.read_text(encoding="utf-8")

    # Filtrar solo sentencias ejecutables (quitar comentarios y líneas vacías)
    statements = []
    current = []
    for line in sql_raw.splitlines():
        stripped = line.strip()
        # Saltar líneas de solo comentario
        if stripped.startswith("--") or stripped == "":
            continue
        current.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(current).strip().rstrip(";")
            if stmt:
                statements.append(stmt)
            current = []

    print(f"[Migration] {len(statements)} sentencias a ejecutar:")
    for i, s in enumerate(statements, 1):
        preview = s.split("\n")[0][:80]
        print(f"  [{i}] {preview}...")

    with db_connection(cfg.db_name) as conn:
        conn.autocommit(False)
        try:
            with conn.cursor() as cur:
                for i, stmt in enumerate(statements, 1):
                    print(f"\n[Migration] Ejecutando [{i}]...")
                    cur.execute(stmt)
                    print(f"  → rowcount={cur.rowcount}")

            conn.commit()
            print("\n[Migration] COMMIT OK — Migración aplicada exitosamente.")

            # Verificar resultado
            with conn.cursor() as cur:
                cur.execute("SELECT nombre, valor FROM secuencias WHERE nombre = 'orden_servicio'")
                row = cur.fetchone()
                if row:
                    print(f"[Verify] secuencias: nombre={row.get('nombre')}, valor={row.get('valor')}")
                    print(f"         → próxima OS será: {str(row.get('valor') + 1).zfill(6)}")
                else:
                    print("[Verify] ADVERTENCIA: fila 'orden_servicio' no encontrada en secuencias")

                cur.execute("SHOW COLUMNS FROM orden_servicio LIKE 'deleted_at'")
                col = cur.fetchone()
                print(f"[Verify] deleted_at: {'EXISTE' if col else 'FALTA'}")

                cur.execute("SHOW COLUMNS FROM orden_servicio LIKE 'deleted_by'")
                col = cur.fetchone()
                print(f"[Verify] deleted_by: {'EXISTE' if col else 'FALTA'}")

        except Exception as e:
            conn.rollback()
            print(f"\n[Migration] ERROR — ROLLBACK: {e}")
            sys.exit(1)


if __name__ == "__main__":
    run()
