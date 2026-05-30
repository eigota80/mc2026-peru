#!/usr/bin/env python3
"""
Pruebas de lógica SQL para el consecutivo global y soft-delete.
Simula el comportamiento de create-order.php y delete-order.php.
Ejecuta en una transacción y hace ROLLBACK al final — no modifica datos reales.

Uso: .venv/bin/python scripts/test_consecutivo.py
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
sys.path.insert(0, str(MCP_DIR))
from server import db_connection, settings  # noqa: E402

PASSED = []
FAILED = []


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        print(f"  ✓ PASS: {label}" + (f" — {detail}" if detail else ""))
        PASSED.append(label)
    else:
        print(f"  ✗ FAIL: {label}" + (f" — {detail}" if detail else ""))
        FAILED.append(label)


def get_next_consecutivo(cur) -> int:
    cur.execute("UPDATE secuencias SET valor = LAST_INSERT_ID(valor + 1) WHERE nombre = 'orden_servicio'")
    if cur.rowcount == 0:
        raise RuntimeError("secuencias no inicializada")
    cur.execute("SELECT LAST_INSERT_ID() AS v")
    return int(cur.fetchone()["v"])


def insert_order(cur, num: str, user: str = "test_user") -> int:
    cur.execute(
        """INSERT INTO orden_servicio
             (numero_os, razon_social, ruc_dni, fecha, moneda, estado, created_by)
           VALUES (%s, 'EMPRESA TEST SA', '20000000001', CURDATE(), 'USD', 'Creada', %s)""",
        (num, user),
    )
    return cur.lastrowid


def soft_delete(cur, row_id: int, user: str = "test_user"):
    cur.execute(
        "UPDATE orden_servicio SET estado='ELIMINADA', deleted_at=NOW(), deleted_by=%s WHERE id=%s",
        (user, row_id),
    )


def run():
    cfg = settings()
    print(f"[Test] DB={cfg.db_name} @ {cfg.ssh_host}\n")

    with db_connection(cfg.db_name) as conn:
        conn.autocommit(False)

        try:
            with conn.cursor() as cur:

                # Estado inicial
                cur.execute("SELECT valor FROM secuencias WHERE nombre='orden_servicio'")
                inicio = int(cur.fetchone()["valor"])
                print(f"[Setup] secuencias.valor inicial = {inicio}")
                print(f"[Setup] próxima OS esperada: {str(inicio+1).zfill(6)}\n")

                # ── Prueba 1: crear una orden ──────────────────────────────
                print("── Prueba 1: Crear una orden ──")
                n1 = get_next_consecutivo(cur)
                num1 = str(n1).zfill(6)
                id1 = insert_order(cur, num1)
                check("Prueba 1 — consecutivo incrementado", n1 == inicio + 1, f"{num1}")
                check("Prueba 1 — orden insertada", id1 > 0, f"id={id1}")
                cur.execute("SELECT numero_os, estado FROM orden_servicio WHERE id=%s", (id1,))
                row = cur.fetchone()
                check("Prueba 1 — numero_os en BD coincide", row["numero_os"] == num1)
                check("Prueba 1 — estado inicial = Creada", row["estado"] == "Creada")
                print()

                # ── Prueba 2: crear 3 órdenes seguidas ────────────────────
                print("── Prueba 2: Crear 3 órdenes consecutivas ──")
                ids2, nums2 = [], []
                for i in range(3):
                    n = get_next_consecutivo(cur)
                    num = str(n).zfill(6)
                    rid = insert_order(cur, num)
                    ids2.append(rid)
                    nums2.append(num)
                    print(f"  Orden {i+1}: {num} (id={rid})")
                check("Prueba 2 — 3 consecutivos únicos", len(set(nums2)) == 3)
                expected = [str(inicio + 2 + i).zfill(6) for i in range(3)]
                check("Prueba 2 — secuencia correcta sin saltos", nums2 == expected, str(nums2))
                print()

                # ── Prueba 3: eliminar orden intermedia ───────────────────
                print("── Prueba 3: Eliminar orden intermedia y crear otra ──")
                id_medio = ids2[1]
                num_medio = nums2[1]
                soft_delete(cur, id_medio)
                cur.execute("SELECT estado, deleted_at FROM orden_servicio WHERE id=%s", (id_medio,))
                del_row = cur.fetchone()
                check("Prueba 3 — estado = ELIMINADA", del_row["estado"] == "ELIMINADA")
                check("Prueba 3 — deleted_at no NULL", del_row["deleted_at"] is not None)

                # Crear otra después de eliminar
                n_post = get_next_consecutivo(cur)
                num_post = str(n_post).zfill(6)
                id_post = insert_order(cur, num_post)
                check("Prueba 3 — número post-borrado NO reutiliza eliminado",
                      num_post != num_medio, f"nuevo={num_post} eliminado={num_medio}")
                check("Prueba 3 — número post-borrado es el siguiente correcto",
                      n_post == inicio + 5, f"esperado={inicio+5} obtenido={n_post}")
                print()

                # ── Prueba 4: verificar UNIQUE KEY ────────────────────────
                print("── Prueba 4: Doble inserción con mismo número debe fallar ──")
                n_dup = get_next_consecutivo(cur)
                num_dup = str(n_dup).zfill(6)
                insert_order(cur, num_dup)
                duplicate_blocked = False
                try:
                    cur.execute(
                        "INSERT INTO orden_servicio (numero_os, razon_social, estado, created_by) "
                        "VALUES (%s, 'DUPLICADA', 'Creada', 'test')",
                        (num_dup,)
                    )
                except Exception:
                    duplicate_blocked = True
                check("Prueba 4 — duplicado bloqueado por UNIQUE KEY", duplicate_blocked)
                print()

                # ── Prueba 5: verificar lista excluye ELIMINADAS ──────────
                print("── Prueba 5: Lista no devuelve órdenes ELIMINADAS ──")
                cur.execute(
                    "SELECT numero_os FROM orden_servicio "
                    "WHERE estado <> 'ELIMINADA' AND deleted_at IS NULL AND id > %s",
                    (inicio + 1,)  # solo las de esta sesión de prueba
                )
                visibles = [r["numero_os"] for r in cur.fetchall()]
                check("Prueba 5 — orden eliminada no aparece en lista",
                      num_medio not in visibles, f"visibles={visibles} eliminado={num_medio}")

                # ── Estado final ───────────────────────────────────────────
                cur.execute("SELECT valor FROM secuencias WHERE nombre='orden_servicio'")
                final_valor = int(cur.fetchone()["valor"])
                print(f"\n[Estado final] secuencias.valor = {final_valor}")

        finally:
            conn.rollback()
            print("\n[Test] ROLLBACK completado — ningún dato de prueba persiste en BD.\n")

    total = len(PASSED) + len(FAILED)
    print(f"{'='*50}")
    print(f"Resultados: {len(PASSED)}/{total} pruebas pasadas")
    if FAILED:
        print(f"Fallidas: {FAILED}")
    else:
        print("Todas las pruebas de lógica SQL pasaron.")
    print(f"{'='*50}")
    sys.exit(1 if FAILED else 0)


if __name__ == "__main__":
    run()
