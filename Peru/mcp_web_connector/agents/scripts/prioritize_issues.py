#!/usr/bin/env python3
"""Prioritize SEO issues from CSV and print a Markdown backlog.

Expected CSV columns are flexible. Useful columns:
issue,hallazgo,action,accion,severity,severidad,impact,impacto,effort,esfuerzo,risk,riesgo,confidence,confianza,owner,responsable,evidence,evidencia
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path
from typing import Any

VALUE_MAP = {
    "critical": 5,
    "critico": 5,
    "crítico": 5,
    "high": 4,
    "alto": 4,
    "medium": 3,
    "medio": 3,
    "low": 2,
    "bajo": 2,
    "none": 1,
    "ninguno": 1,
    "": 0,
}

EFFORT_MAP = {
    "very low": 1,
    "muy bajo": 1,
    "low": 2,
    "bajo": 2,
    "medium": 3,
    "medio": 3,
    "high": 4,
    "alto": 4,
    "very high": 5,
    "muy alto": 5,
    "": 3,
}


def pick(row: dict[str, str], *names: str) -> str:
    lower = {k.lower().strip(): v.strip() for k, v in row.items() if k is not None and v is not None}
    for name in names:
        if name in lower and lower[name]:
            return lower[name]
    return ""


def val(text: str, default: int = 3) -> int:
    return VALUE_MAP.get(text.lower().strip(), default)


def effort_val(text: str) -> int:
    return EFFORT_MAP.get(text.lower().strip(), 3)


def score(row: dict[str, str]) -> float:
    severity = val(pick(row, "severity", "severidad"), 3)
    impact = val(pick(row, "impact", "impacto"), 3)
    confidence = val(pick(row, "confidence", "confianza"), 3)
    risk = val(pick(row, "risk", "riesgo"), 2)
    effort = effort_val(pick(row, "effort", "esfuerzo"))
    return round((severity * 2.0) + (impact * 2.0) + confidence + risk - (effort * 0.8), 2)



def tier(row: dict[str, str]) -> int:
    severity = val(pick(row, "severity", "severidad"), 3)
    if severity >= 5:
        return 1
    if severity >= 4:
        return 2
    if severity >= 3:
        return 3
    return 4


def render(rows: list[dict[str, str]]) -> str:
    ranked = sorted(rows, key=lambda row: (tier(row), -score(row)))
    lines = [
        "| Prioridad | Score | Issue | Severidad | Impacto | Esfuerzo | Accion | Responsable | Evidencia |",
        "|---:|---:|---|---|---|---|---|---|---|",
    ]
    for i, row in enumerate(ranked, 1):
        issue = pick(row, "issue", "hallazgo", "problema", "task", "tarea")
        action = pick(row, "action", "accion", "acción", "recommendation", "recomendacion", "recomendación")
        severity = pick(row, "severity", "severidad")
        impact = pick(row, "impact", "impacto")
        effort = pick(row, "effort", "esfuerzo")
        owner = pick(row, "owner", "responsable")
        evidence = pick(row, "evidence", "evidencia")
        lines.append(f"| {i} | {score(row)} | {issue} | {severity} | {impact} | {effort} | {action} | {owner} | {evidence} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: prioritize_issues.py issues.csv", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        with path.open(newline="", encoding="utf-8-sig") as fh:
            rows = list(csv.DictReader(fh))
    except Exception as exc:
        print(f"error reading csv: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("error: csv has no rows", file=sys.stderr)
        return 1
    print(render(rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
