#!/usr/bin/env python3
"""Baixa população residente estimada (IBGE/SIDRA Tabela 6579, variável 9324)
para TODOS os 5.570 municípios brasileiros.

Estratégia: SIDRA recusa N6 sem filtro (HTTP 500). Iteramos por UF (27 chamadas),
N6[lista de munis dentro da UF]. Cada chamada fica pequena.

Output: data/fallback/ibge_populacao_municipios.json — formato idêntico ao
data/fallback/ibge_populacao_uf.json (JSON-as-list[1] com .resultados[].series[]).

Para anos sem publicação IBGE (geralmente 2022 e 2023, anos do Censo), usa-se
extrapolação linear no LOAD do dado (build_fallback_municipal_gold.py), não
aqui — este script preserva exatamente o que IBGE retornou.

Versão atual: 2026-04 — usa também:
  - IBGE Localidades v1 → lista canônica dos 5.571 (DF é tratado como UF
    única, com 1 município = 5300108 Brasília).
  - kelvins/Municipios-Brasileiros (CSV) → lat/lon dos centroides
    (referência canônica em open data brasileiro).
"""
from __future__ import annotations

import csv
import gzip
import io
import json
import time
import urllib.request
import urllib.error
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_POP_JSON  = ROOT / "data" / "fallback" / "ibge_populacao_municipios.json"
OUT_REF_CSV   = ROOT / "data" / "reference" / "ibge_municipios.csv"

YEARS_RANGE = "2013-2025"

UFS_27 = {
    11:"RO", 12:"AC", 13:"AM", 14:"RR", 15:"PA", 16:"AP", 17:"TO",
    21:"MA", 22:"PI", 23:"CE", 24:"RN", 25:"PB", 26:"PE", 27:"AL", 28:"SE", 29:"BA",
    31:"MG", 32:"ES", 33:"RJ", 35:"SP",
    41:"PR", 42:"SC", 43:"RS",
    50:"MS", 51:"MT", 52:"GO", 53:"DF",
}

UF_REGIAO = {
    "AC":"Norte","AL":"Nordeste","AM":"Norte","AP":"Norte","BA":"Nordeste",
    "CE":"Nordeste","DF":"Centro-Oeste","ES":"Sudeste","GO":"Centro-Oeste",
    "MA":"Nordeste","MG":"Sudeste","MS":"Centro-Oeste","MT":"Centro-Oeste",
    "PA":"Norte","PB":"Nordeste","PE":"Nordeste","PI":"Nordeste","PR":"Sul",
    "RJ":"Sudeste","RN":"Nordeste","RO":"Norte","RR":"Norte","RS":"Sul",
    "SC":"Sul","SE":"Nordeste","SP":"Sudeste","TO":"Norte",
}


def http_get(url: str, retries: int = 3, timeout: int = 180) -> bytes:
    headers = {
        "User-Agent": "mirante-dos-dados/1.0 wp7-municipal",
        "Accept": "application/json",
        "Accept-Encoding": "gzip",
    }
    last_exc = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if r.headers.get("content-encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return raw
        except (urllib.error.URLError, urllib.error.HTTPError) as e:
            last_exc = e
            time.sleep(1.5 * (i + 1))
    raise RuntimeError(f"falhou {url}: {last_exc}")


def fetch_ibge_localidades() -> list[dict]:
    """5.571 munis canônicos (id 7-dig, nome, hierarquia)."""
    raw = http_get("https://servicodados.ibge.gov.br/api/v1/localidades/municipios")
    return json.loads(raw.decode("utf-8"))


def fetch_kelvins_coords() -> dict[str, tuple[float, float, int]]:
    """{cod_ibge: (lat, lon, capital)}."""
    raw = http_get(
        "https://raw.githubusercontent.com/kelvins/municipios-brasileiros/main/csv/municipios.csv"
    )
    txt = raw.decode("utf-8")
    out = {}
    for r in csv.DictReader(io.StringIO(txt)):
        out[r["codigo_ibge"]] = (
            float(r["latitude"]), float(r["longitude"]), int(r["capital"]),
        )
    return out


def fetch_sidra_pop_for_uf(cod_uf_2digits: int, muni_ids: list[str]) -> list[dict]:
    """SIDRA 6579/9324 para todos os munis da UF."""
    ids_str = ",".join(muni_ids)
    url = (
        "https://servicodados.ibge.gov.br/api/v3/agregados/6579/"
        f"periodos/{YEARS_RANGE}/variaveis/9324?localidades=N6[{ids_str}]"
    )
    raw = http_get(url, timeout=240)
    payload = json.loads(raw.decode("utf-8"))
    if not payload:
        return []
    return payload[0]["resultados"][0]["series"]


def main():
    print("== 1/3 IBGE Localidades v1 (5.571 munis) ==")
    munis = fetch_ibge_localidades()
    print(f"  {len(munis):,} munis")

    # Agrupar por UF — UF derivada do cod_uf (2 primeiros dígitos do cod_muni 7-dig)
    by_uf: dict[str, list[dict]] = defaultdict(list)
    for m in munis:
        cod = int(m["id"])
        cod_uf_int = cod // 100000  # 11..53
        sigla = UFS_27.get(cod_uf_int)
        if not sigla:
            print(f"  ⚠ ignorando muni {cod} (UF code {cod_uf_int} não reconhecida)")
            continue
        by_uf[sigla].append(m)
    print(f"  UFs: {len(by_uf)} ({sorted(by_uf)})")

    print("== 2/3 kelvins/Municipios-Brasileiros (lat/lon centroides) ==")
    coords = fetch_kelvins_coords()
    print(f"  {len(coords):,} munis com lat/lon")
    coverage = sum(1 for m in munis if str(m["id"]) in coords)
    print(f"  cobertura: {coverage}/{len(munis)} ({coverage/len(munis):.1%})")

    print(f"== 3/3 SIDRA 6579 (var 9324) — pop {YEARS_RANGE} por UF, chunked ==")
    CHUNK_MAX = 200  # SIDRA recusa requests grandes (HTTP 500 em MG=853, SP=645)
    all_series = []
    for sigla in sorted(by_uf):
        ms = by_uf[sigla]
        ids_full = [str(m["id"]) for m in ms]
        chunks = [ids_full[i:i+CHUNK_MAX] for i in range(0, len(ids_full), CHUNK_MAX)]
        ser_uf = []
        for ci, chunk in enumerate(chunks):
            try:
                ser_uf.extend(fetch_sidra_pop_for_uf(0, chunk))
            except Exception as e:
                print(f"  {sigla} chunk {ci+1}/{len(chunks)} FALHOU "
                      f"({type(e).__name__}) — pular")
        all_series.extend(ser_uf)
        n_anos = len(ser_uf[0]["serie"]) if ser_uf else 0
        chunk_str = f" ({len(chunks)} chunks)" if len(chunks) > 1 else ""
        print(f"  {sigla}: {len(ms):>3} munis → {len(ser_uf):>3} séries, ~{n_anos} anos{chunk_str}")

    # Reembalar no formato SIDRA padrão (mesmo do UF fallback)
    payload = [{
        "id": "9324",
        "variavel": "População residente estimada",
        "unidade": "Pessoas",
        "resultados": [{"classificacoes": [], "series": all_series}],
    }]
    OUT_POP_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_POP_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    # Cobertura por ano
    years_seen = defaultdict(int)
    for s in all_series:
        for y in s["serie"]:
            years_seen[y] += 1
    print(f"\n  cobertura ano × munis (pop não-nula):")
    for y in sorted(years_seen):
        n_naonula = sum(1 for s in all_series if s["serie"].get(y) and s["serie"].get(y) != "...")
        print(f"    {y}: {years_seen[y]:>5} munis (não-nulo: {n_naonula:,})")
    print(f"  ✔ {OUT_POP_JSON.relative_to(ROOT)} ({OUT_POP_JSON.stat().st_size:,} bytes)")

    # Reference CSV — 5.570+ munis com cod, nome, uf, regiao, lat, lon, capital
    OUT_REF_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_REF_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "cod_municipio", "municipio", "uf", "regiao",
            "lat", "lon", "capital",
        ])
        w.writeheader()
        for m in munis:
            cod = str(m["id"])
            cod_uf_int = int(cod) // 100000
            uf = UFS_27.get(cod_uf_int)
            if not uf: continue
            reg = UF_REGIAO[uf]
            ll = coords.get(cod, (None, None, 0))
            w.writerow({
                "cod_municipio": cod,
                "municipio":     m["nome"],
                "uf":            uf,
                "regiao":        reg,
                "lat":           ll[0] if ll[0] is not None else "",
                "lon":           ll[1] if ll[1] is not None else "",
                "capital":       ll[2],
            })
    print(f"  ✔ {OUT_REF_CSV.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
