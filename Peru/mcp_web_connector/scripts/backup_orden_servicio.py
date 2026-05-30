#!/usr/bin/env python3
"""
Fase 1 — Exportación de solo lectura via MCP mcperu-web.
Importa server.py directamente en el mismo proceso.
Solo SELECT/SHOW/DESCRIBE. Credenciales manejadas por server.py desde .env.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ── Monkey-patch ANTES de importar server.py ────────────────────────────────
# paramiko 5.x eliminó DSSKey; sshtunnel 0.4.0 lo referencia al importar.
# Este stub evita el AttributeError sin afectar funcionalidad RSA/ED25519.
import paramiko as _paramiko
if not hasattr(_paramiko, "DSSKey"):
    _paramiko.DSSKey = type("DSSKey", (_paramiko.PKey,), {
        "get_name": lambda self: "ssh-dss",
        "asbytes": lambda self: b"",
        "sign_ssh_data": lambda self, m, k=None: b"",
        "verify_ssh_sig": lambda self, m, msg: False,
        "get_bits": lambda self: 0,
        "_from_private_key": classmethod(lambda cls, f, pw=None: cls()),
        "_from_private_key_file": classmethod(lambda cls, f, pw=None: cls()),
    })

# ── Ahora sí importar server.py (sshtunnel carga con DSSKey parcheado) ──────
MCP_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(MCP_DIR))
from server import db_connection, fetch_rows, public_settings  # noqa: E402

BACKUP_DIR = Path.home() / f"mcperu_mariadb_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
DB_NAME = "bdmcperu"


def run_query(sql: str, params=None, max_rows: int = 500) -> dict:
    with db_connection(DB_NAME) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            rows = cur.fetchmany(max_rows + 1)
            truncated = len(rows) > max_rows
            rows = rows[:max_rows]
            columns = [d[0] for d in (cur.description or [])]
    return {"columns": columns, "rows": list(rows), "truncated": truncated}


def save_text(filename: str, content: str) -> Path:
    path = BACKUP_DIR / filename
    path.write_text(content, encoding="utf-8")
    return path


def save_json(filename: str, data) -> Path:
    return save_text(filename, json.dumps(data, ensure_ascii=False, indent=2, default=str))


def save_gz(filename: str, content: str) -> Path:
    path = BACKUP_DIR / filename
    path.write_bytes(gzip.compress(content.encode("utf-8"), compresslevel=9))
    return path


def rows_to_text(result: dict) -> str:
    cols = result.get("columns", [])
    rows = result.get("rows", [])
    lines = ["\t".join(str(c) for c in cols)]
    for row in rows:
        if isinstance(row, dict):
            lines.append("\t".join("" if row.get(c) is None else str(row[c]) for c in cols))
        else:
            lines.append("\t".join("" if v is None else str(v) for v in row))
    if result.get("truncated"):
        lines.append("\n[TRUNCADO — hay más filas]")
    return "\n".join(lines)


def show_create_table(table: str) -> str:
    result = run_query(f"SHOW CREATE TABLE `{table}`", max_rows=1)
    if result["rows"]:
        row0 = result["rows"][0]
        if isinstance(row0, dict):
            return str(row0.get("Create Table") or list(row0.values())[-1] or "")
        return str(row0[1]) if len(row0) > 1 else ""
    return ""


def main():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    cfg = public_settings()
    print(f"[Fase 1] Carpeta: {BACKUP_DIR}")
    print(f"[OK] DB={cfg.get('db_name')} SSH={cfg.get('ssh_host')} user={cfg.get('db_user')}")
    save_json("config_summary.json", cfg)

    all_candidates = []
    TABLE_ORDERS = None
    total = 0
    consec_field = None
    max_consec_val = None
    col_names = []

    # ── 1. SHOW TABLES ─────────────────────────────────────────────────────────
    print("[1/8] Listando tablas...")
    r = run_query("SHOW TABLES", max_rows=300)
    table_names = [list(row.values())[0] if isinstance(row, dict) else row[0]
                   for row in r["rows"]]
    save_text("tablas_disponibles.txt", "\n".join(table_names))
    save_json("tablas_disponibles.json", {"tables": table_names})
    print(f"    → {len(table_names)} tablas: {table_names}")

    # ── 2. CANDIDATAS POR NOMBRE ───────────────────────────────────────────────
    print("[2/8] Buscando tablas candidatas...")
    candidatas = []
    for pattern in ("%orden%", "%servicio%", "%_os", "os_%", "%secuencia%", "%correlativo%", "%consecutivo%"):
        r2 = run_query("SHOW TABLES LIKE %s", (pattern,), max_rows=50)
        found = [list(row.values())[0] if isinstance(row, dict) else row[0]
                 for row in r2["rows"]]
        candidatas.extend(found)
    candidatas = list(dict.fromkeys(candidatas))
    save_text("tablas_candidatas.txt", "\n".join(candidatas) if candidatas else "(ninguna)")
    print(f"    → Candidatas: {candidatas}")

    # ── 3. INFORMATION_SCHEMA ──────────────────────────────────────────────────
    print("[3/8] Buscando columnas clave...")
    r3 = run_query(
        "SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE "
        "FROM information_schema.COLUMNS "
        "WHERE TABLE_SCHEMA = %s "
        "AND (LOWER(COLUMN_NAME) LIKE %s OR LOWER(COLUMN_NAME) LIKE %s "
        "  OR LOWER(COLUMN_NAME) LIKE %s OR LOWER(COLUMN_NAME) LIKE %s "
        "  OR LOWER(TABLE_NAME) LIKE %s OR LOWER(TABLE_NAME) LIKE %s) "
        "ORDER BY TABLE_NAME, ORDINAL_POSITION",
        (DB_NAME, "%orden%", "%nro%", "%numero%", "%correlativ%", "%orden%", "%servicio%"),
        max_rows=500,
    )
    save_json("info_schema_columnas_candidatas.json", r3)
    tables_schema = list(dict.fromkeys(
        (row.get("TABLE_NAME") if isinstance(row, dict) else row[0])
        for row in r3["rows"]
    ))
    all_candidates = list(dict.fromkeys(candidatas + tables_schema))
    save_text("tablas_secuencias_candidatas.txt",
              "\n".join(all_candidates) if all_candidates else "(ninguna)")
    print(f"    → Candidatas totales: {all_candidates}")

    TABLE_ORDERS = all_candidates[0] if all_candidates else None
    print(f"    → Tabla principal: {TABLE_ORDERS}")

    if not TABLE_ORDERS:
        print("[!] No hay tabla candidata. Ver tablas_disponibles.txt")

    # ── 4. DESCRIBE + SHOW CREATE TABLE ───────────────────────────────────────
    if TABLE_ORDERS:
        print(f"[4/8] Describiendo `{TABLE_ORDERS}`...")
        r_desc = run_query(f"DESCRIBE `{TABLE_ORDERS}`", max_rows=300)
        save_text(f"{TABLE_ORDERS}_describe.txt", rows_to_text(r_desc))
        save_json(f"{TABLE_ORDERS}_describe.json", r_desc)
        col_names = [
            (row.get("Field") if isinstance(row, dict) else row[0])
            for row in r_desc["rows"]
        ]
        print(f"    → Columnas ({len(col_names)}): {col_names}")

        create_sql = show_create_table(TABLE_ORDERS)
        save_text(f"{TABLE_ORDERS}_schema_show_create.sql",
                  f"-- SHOW CREATE TABLE `{TABLE_ORDERS}`\n\n{create_sql}\n")
        save_text(f"{TABLE_ORDERS}_schema.sql",
                  f"-- Schema de `{TABLE_ORDERS}` — Fase 1 (solo lectura)\n\n{create_sql};\n")
        print("    → Schema guardado")

        # ── 5. EXPORT DATOS ────────────────────────────────────────────────────
        print(f"[5/8] Exportando datos de `{TABLE_ORDERS}`...")
        r_data = run_query(f"SELECT * FROM `{TABLE_ORDERS}` ORDER BY 1", max_rows=500)
        data_cols = r_data["columns"]
        data_rows = r_data["rows"]
        save_gz(f"{TABLE_ORDERS}_full_export.tsv.gz", rows_to_text(r_data))

        sql_lines = [f"-- Datos de `{TABLE_ORDERS}` — {len(data_rows)} filas\n"]
        for row in data_rows:
            vals = []
            for col in data_cols:
                v = row.get(col) if isinstance(row, dict) else None
                if v is None:
                    vals.append("NULL")
                elif isinstance(v, (int, float)):
                    vals.append(str(v))
                else:
                    vals.append("'" + str(v).replace("\\", "\\\\").replace("'", "\\'") + "'")
            sql_lines.append(
                f"INSERT INTO `{TABLE_ORDERS}` "
                f"({', '.join('`' + c + '`' for c in data_cols)}) "
                f"VALUES ({', '.join(vals)});"
            )
        save_gz(f"{TABLE_ORDERS}_data.sql.gz", "\n".join(sql_lines))
        print(f"    → {len(data_rows)} filas exportadas")

        # ── 6. DIAGNÓSTICO ─────────────────────────────────────────────────────
        print(f"[6/8] Conteo total...")
        r_count = run_query(f"SELECT COUNT(*) AS total FROM `{TABLE_ORDERS}`", max_rows=1)
        total = list(r_count["rows"][0].values())[0] if r_count["rows"] else 0
        save_text(f"{TABLE_ORDERS}_count.txt", f"total_registros: {total}\n")
        print(f"    → Total: {total}")

        print(f"[7/8] Últimos 20 + consecutivo + estados...")
        r_last = run_query(f"SELECT * FROM `{TABLE_ORDERS}` ORDER BY 1 DESC", max_rows=20)
        save_text(f"{TABLE_ORDERS}_ultimos_20.txt", rows_to_text(r_last))

        consec_kw = ["numero", "nro", "correlativ", "consecutiv", "folio", "order_num", "num_orden"]
        consec_candidates = [c for c in col_names if any(k in c.lower() for k in consec_kw)]
        print(f"    → Campos consecutivo candidatos: {consec_candidates}")

        for field in consec_candidates:
            try:
                r_max = run_query(f"SELECT MAX(`{field}`) AS max_consecutivo FROM `{TABLE_ORDERS}`",
                                  max_rows=1)
                val = list(r_max["rows"][0].values())[0] if r_max["rows"] else None
                if val is not None:
                    max_consec_val, consec_field = val, field
                    save_text(f"{TABLE_ORDERS}_max_consecutivo.txt",
                              f"campo: {field}\nmax_consecutivo: {val}\n")
                    print(f"    → MAX(`{field}`) = {val}")
                    break
            except Exception as e:
                print(f"    [!] MAX(`{field}`): {e}")

        if consec_field is None and any(c.lower() == "id" for c in col_names):
            try:
                r_max = run_query(f"SELECT MAX(`id`) AS max_id FROM `{TABLE_ORDERS}`", max_rows=1)
                val = list(r_max["rows"][0].values())[0] if r_max["rows"] else None
                save_text(f"{TABLE_ORDERS}_max_consecutivo.txt",
                          f"campo: id (fallback — sin campo de consecutivo específico)\nmax_id: {val}\n")
                print(f"    → MAX(id) = {val}")
            except Exception as e:
                save_text(f"{TABLE_ORDERS}_max_consecutivo.txt", f"error: {e}\n")

        estado_fields = [c for c in col_names if "estado" in c.lower() or "status" in c.lower()]
        if estado_fields:
            fe = estado_fields[0]
            try:
                r_est = run_query(
                    f"SELECT `{fe}`, COUNT(*) AS total FROM `{TABLE_ORDERS}` "
                    f"GROUP BY `{fe}` ORDER BY total DESC",
                    max_rows=50,
                )
                save_text(f"{TABLE_ORDERS}_estados.txt", rows_to_text(r_est))
                print(f"    → Estados ({fe}): {[list(r.values()) for r in r_est['rows']]}")
            except Exception as e:
                save_text(f"{TABLE_ORDERS}_estados.txt", f"error: {e}\n")
        else:
            save_text(f"{TABLE_ORDERS}_estados.txt", "(sin campo de estado)\n")
            print("    → Sin campo de estado")

    # ── 8. MANIFEST + CHECKSUMS ────────────────────────────────────────────────
    print("[8/8] Manifest y checksums...")
    manifest_lines, checksums_lines = [], []
    for f in sorted(BACKUP_DIR.iterdir()):
        size = f.stat().st_size
        manifest_lines.append(f"{f.name:<70} {size:>10} bytes")
        digest = hashlib.sha256(f.read_bytes()).hexdigest()
        checksums_lines.append(f"{digest}  {f.name}")
    save_text("manifest_archivos.txt", "\n".join(manifest_lines) + "\n")
    save_text("checksums_sha256.txt", "\n".join(checksums_lines) + "\n")

    suspicious = []
    for f in BACKUP_DIR.iterdir():
        if f.suffix == ".gz":
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        hits = re.findall(r"(?:password|DB_PASS|secret)\s*[=:]\s*\S{4,}", content, re.IGNORECASE)
        real = [h for h in hits if not any(x in h.lower() for x in ["***", "redact", "example", "false", "true", "null"])]
        if real:
            suspicious.append(f.name)
    if suspicious:
        print(f"[!] REVISAR posibles credenciales en: {suspicious}")
    else:
        print("[OK] Seguridad: sin credenciales en archivos exportados.")

    print(f"\n{'='*64}")
    print(f"Fase 1 completada.")
    print(f"Carpeta: {BACKUP_DIR}")
    print(f"Archivos: {len(list(BACKUP_DIR.iterdir()))}")
    if TABLE_ORDERS:
        print(f"Tabla principal: {TABLE_ORDERS}")
        print(f"Total registros: {total}")
        if consec_field:
            print(f"Max consecutivo ({consec_field}): {max_consec_val}")
    print(f"{'='*64}\n")

    return {
        "backup_dir": str(BACKUP_DIR),
        "table": TABLE_ORDERS,
        "all_candidates": all_candidates,
        "total": total,
        "consec_field": consec_field,
        "max_consec": max_consec_val,
        "columns": col_names,
    }


if __name__ == "__main__":
    result = main()
    print(json.dumps(result, indent=2, default=str))
