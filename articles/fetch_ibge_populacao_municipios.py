#!/usr/bin/env python3
"""Baixa população residente estimada (IBGE/SIDRA Tabela 6579, variável 9324)
para o subset de municípios em data/reference/ibge_municipios_sample.csv.

Output: data/fallback/ibge_populacao_municipios.json no MESMO formato do
data/fallback/ibge_populacao_uf.json (JSON-as-list[1] com .resultados[].series[]
{localidade: {id, nivel, nome}, serie: {ano_str: pop_str}}).

Endpoint: https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{anos}/variaveis/9324?localidades=N6[ids]
Limite: ~1000 munis por chamada; nosso subset (100) entra em uma única request.

Para o pipeline Databricks, ver pipelines/notebooks/ingest/ibge_municipios_meta.py
(que faz o mesmo pra todos os 5.570 munis e grava em
bronze.ibge_municipios_populacao_raw).
"""
from __future__ import annotations

import csv
import json
import urllib.request
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REF_CSV = ROOT / "data" / "reference" / "ibge_municipios_sample.csv"
OUT_JSON = ROOT / "data" / "fallback" / "ibge_populacao_municipios.json"

YEARS_RANGE = "2013-2025"
SIDRA_URL = (
    "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/{anos}"
    "/variaveis/9324?localidades=N6[{ids}]"
)


def load_munis():
    out = []
    with REF_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.append((r["cod_municipio"], r["municipio"], r["uf"]))
    return out


def fetch(ids: list[str]) -> dict:
    url = SIDRA_URL.format(anos=YEARS_RANGE, ids=",".join(ids))
    print(f"GET {url[:120]}…")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "mirante-dos-dados/1.0 wp7-fallback",
                 "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    munis = load_munis()
    ids = [m[0] for m in munis]
    print(f"Buscando SIDRA 6579 (var 9324) {YEARS_RANGE} para {len(ids)} munis…")

    try:
        payload = fetch(ids)
    except urllib.error.URLError as e:
        print(f"⚠ Sem rede pra IBGE/SIDRA ({e}). Saída: arquivo não criado.")
        print(f"  Use o pipeline Databricks pipelines/notebooks/ingest/ibge_municipios_meta.py")
        print(f"  que tem retries e roda em ambiente com saída pra IBGE.")
        return 1
    except Exception as e:
        print(f"⚠ Erro ao buscar SIDRA: {type(e).__name__}: {e}")
        return 1

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    # Sanity check
    series = payload[0]["resultados"][0]["series"] if payload else []
    print(f"✔ {OUT_JSON.relative_to(ROOT)} ({OUT_JSON.stat().st_size:,} bytes)")
    print(f"  munis retornados: {len(series)} (esperado {len(ids)})")
    if series:
        s0 = series[0]
        anos = sorted(s0["serie"].keys())
        print(f"  exemplo munis[0]: {s0['localidade']['nome']} ({s0['localidade']['id']}) "
              f"anos {anos[0]}..{anos[-1]} ({len(anos)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
