#!/usr/bin/env python3
"""Merge platform_stats.json from Databricks Volume with local repo version.

Used by .github/workflows/auto-sync-gold.yml to avoid clobbering local patches
when the export pipeline (platform_stats_json.py on Databricks) lags behind
local edits — e.g., when we manually patch verticals.finops or
verticals.rais.silver_bytes here while waiting for the next bundle deploy
to refresh the Volume copy.

Decision rule:
- If the VOLUME copy is at least as complete as LOCAL (all completeness
  checks pass), use Volume — it's the authoritative refresh.
- Else, preserve LOCAL — Volume is stale, refresh hasn't propagated yet.
- If LOCAL is missing too (fresh checkout), use Volume regardless.

Completeness checks (one stage at a time as the export pipeline grows):
- verticals.finops present (added 2026-04-28)
- verticals.rais.delta_bronze_rows > 0 (RAIS bronze ran)
- verticals.rais.intermediate_files > 0 (TXT extracted)
- silver_bytes / gold_bytes per vertical (added 2026-04-28)
"""
from __future__ import annotations
import json
import shutil
import sys
from pathlib import Path


def is_complete(stats):
    """Return (per-check dict, overall bool)."""
    v = stats.get("verticals", {}) or {}
    rais = v.get("rais", {}) or {}
    checks = {
        "finops_present":        "finops" in v,
        "rais_bronze_present":   (rais.get("delta_bronze_rows", 0) or 0) > 0,
        "rais_txt_present":      (rais.get("intermediate_files", 0) or 0) > 0,
        "silver_bytes_per_vert": any(
            "silver_bytes" in (v.get(k, {}) or {})
            for k in ("pbf", "rais", "equipamentos", "uropro", "emendas")
        ),
    }
    return checks, all(checks.values())


def main(argv):
    if len(argv) != 3:
        print("usage: sync-merge-platform-stats.py <volume.json> <local.json>", file=sys.stderr)
        return 2
    vol_path = Path(argv[1])
    loc_path = Path(argv[2])

    if not vol_path.exists():
        print(f"  ⚠ {vol_path} ausente — preservando local")
        return 0
    if not loc_path.exists():
        print(f"  → {loc_path} ausente — copiando do Volume direto")
        shutil.copy(vol_path, loc_path)
        return 0

    try:
        volume = json.loads(vol_path.read_text())
        local  = json.loads(loc_path.read_text())
    except Exception as e:
        print(f"  ⚠ falha parseando JSON ({e}) — preservando local")
        return 0

    vol_checks, vol_ok = is_complete(volume)
    loc_checks, loc_ok = is_complete(local)
    print(f"  volume completeness: {vol_checks} → ok={vol_ok}")
    print(f"  local  completeness: {loc_checks} → ok={loc_ok}")

    if vol_ok:
        shutil.copy(vol_path, loc_path)
        print(f"  ✓ Volume completo — platform_stats.json sincado")
    elif not loc_ok:
        # Both stale; trust Volume as authoritative
        shutil.copy(vol_path, loc_path)
        print(f"  → ambos incompletos, usando Volume mesmo assim")
    else:
        print(f"  ⚠ Volume STALE (export pipeline lagging) — preservando local")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
