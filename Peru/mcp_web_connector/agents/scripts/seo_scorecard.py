#!/usr/bin/env python3
"""Generate a weighted SEO scorecard from a JSON findings file.

Input JSON example:
{
  "site": "example.com",
  "scores": {
    "technical_indexing": 70,
    "content_intent": 60,
    "performance_ux": 55,
    "authority_trust": 50,
    "organic_conversion": 65,
    "measurement": 40
  },
  "critical_issues": ["spam indexed"],
  "recommendations": [
    {"category": "technical", "action": "clean spam URLs", "impact": "high", "effort": "medium"}
  ]
}
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

WEIGHTS = {
    "technical_indexing": 30,
    "content_intent": 25,
    "performance_ux": 15,
    "authority_trust": 15,
    "organic_conversion": 10,
    "measurement": 5,
}

LABELS = {
    "technical_indexing": "Técnico e indexación",
    "content_intent": "Contenido e intención",
    "performance_ux": "Rendimiento y UX",
    "authority_trust": "Autoridad y confianza",
    "organic_conversion": "Conversión orgánica",
    "measurement": "Medición",
}


def clamp_score(value: Any) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(100.0, number))


def weighted_score(scores: dict[str, Any]) -> float:
    total = 0.0
    for key, weight in WEIGHTS.items():
        total += clamp_score(scores.get(key, 0)) * weight / 100
    return round(total, 1)


def apply_critical_cap(score: float, issues: list[Any]) -> tuple[float, str | None]:
    issue_text = " ".join(str(issue).lower() for issue in issues)
    caps = [
        (40.0, ["spam", "hack", "malware", "cloaking", "contenido inyectado"], "posible spam, hackeo, malware o cloaking"),
        (50.0, ["noindex", "robots", "canonical incorrecto", "bloqueo"], "bloqueo de indexación o canonical crítico"),
        (60.0, ["duplicación masiva", "duplicacion masiva", "parámetros masivos", "parametros masivos"], "duplicación masiva de URLs"),
        (70.0, ["sin medición", "sin medicion", "no search console", "no ga4"], "medición insuficiente"),
    ]
    for cap, terms, reason in caps:
        if any(term in issue_text for term in terms):
            return min(score, cap), reason
    return score, None


def render_markdown(data: dict[str, Any]) -> str:
    site = data.get("site", "sitio web")
    scores = data.get("scores", {}) if isinstance(data.get("scores", {}), dict) else {}
    issues = data.get("critical_issues", [])
    if not isinstance(issues, list):
        issues = [issues]
    recommendations = data.get("recommendations", [])
    if not isinstance(recommendations, list):
        recommendations = []

    raw_score = weighted_score(scores)
    final_score, cap_reason = apply_critical_cap(raw_score, issues)

    lines = [
        f"# Scorecard SEO: {site}",
        "",
        f"**Puntuación ponderada:** {final_score}/100",
    ]
    if cap_reason:
        lines.append(f"**Nota:** la puntuación fue limitada por {cap_reason}.")
    lines.extend(["", "## Desglose", "", "| Área | Peso | Score |", "|---|---:|---:|"])
    for key, weight in WEIGHTS.items():
        lines.append(f"| {LABELS[key]} | {weight}% | {clamp_score(scores.get(key, 0)):.0f}/100 |")

    if issues:
        lines.extend(["", "## Riesgos críticos", ""])
        for issue in issues:
            lines.append(f"- {issue}")

    if recommendations:
        lines.extend(["", "## Recomendaciones priorizadas", "", "| Categoría | Acción | Impacto | Esfuerzo |", "|---|---|---|---|"])
        for rec in recommendations:
            if isinstance(rec, dict):
                lines.append(
                    f"| {rec.get('category', '')} | {rec.get('action', '')} | {rec.get('impact', '')} | {rec.get('effort', '')} |"
                )
            else:
                lines.append(f"| general | {rec} |  |  |")

    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: seo_scorecard.py findings.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"error reading json: {exc}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("error: top-level JSON must be an object", file=sys.stderr)
        return 1
    print(render_markdown(data))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
