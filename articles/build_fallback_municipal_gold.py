#!/usr/bin/env python3
"""Constrói fallback gold municipal para o WP#7 (Bolsa Família por Município).

CONTEXTO. Este script gera uma versão LOCAL e TRANSPARENTE do gold municipal
quando o pipeline completo de Databricks (silver/pbf_total_municipio_mes →
gold/pbf_municipios_df → export/pbf_municipios_df_json) ainda não rodou.

ENTRADAS (todas reais e públicas):
  1. data/gold/gold_pbf_estados_df.json — gold UF × Ano com totais reais (CGU)
  2. data/reference/ibge_municipios_sample.csv — 100 municípios representativos
     (27 capitais + 73 cidades grandes/médias) com:
       - cod_municipio (IBGE 7 dígitos com DV)
       - lat, lon (centroide IBGE/MalhaDigital)
       - populacao_2022 (Censo IBGE 2022)
       - idhm_2010 (Atlas Brasil — PNUD/IPEA/FJP)
       - linha_pobreza_2010 (% pop com renda < linha de pobreza extrema, Atlas)

ALOCAÇÃO (transparente, não fabricada):
  Para cada (UF, Ano), distribuímos o total UF (do gold real) entre os munis
  da amostra na UF, ponderando por w_uf,muni = pop_muni × pobreza_muni.
  A alocação reflete a lógica oficial do PBF (focalização por renda
  per capita), produzindo uma série municipal CONSISTENTE com a série UF
  oficial. NÃO substitui o pipeline Databricks com microdados; SUBSTITUI o
  papel demonstrativo das figuras locais quando o gold prod ainda não foi
  exportado.

SAÍDAS:
  data/fallback/gold_pbf_municipios_df.json
    Schema:
      Ano, cod_municipio, municipio, uf, regiao, lat, lon, populacao,
      n_benef (alocado), valor_nominal (R$ mi), valor_2021 (R$ mi),
      pbfPerBenef, pbfPerCapita, idhm_2010, _source ('fallback'|'production')
"""
import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLD_UF = ROOT / "data" / "gold" / "gold_pbf_estados_df.json"
REF_CSV = ROOT / "data" / "reference" / "ibge_municipios_sample.csv"
POP_MUN = ROOT / "data" / "fallback" / "ibge_populacao_municipios.json"
OUT_JSON = ROOT / "data" / "fallback" / "gold_pbf_municipios_df.json"
OUT_JSON.parent.mkdir(parents=True, exist_ok=True)


def load_pop_muni_serie():
    """Carrega população real IBGE/SIDRA por (cod_municipio, ano) — mesmo
    formato do data/fallback/ibge_populacao_uf.json para municípios."""
    if not POP_MUN.exists():
        print(f"⚠ {POP_MUN.name} ausente — rode articles/fetch_ibge_populacao_municipios.py primeiro.")
        return None
    payload = json.loads(POP_MUN.read_text(encoding="utf-8"))
    series = payload[0]["resultados"][0]["series"]
    out = {}  # (cod, ano) -> populacao
    for s in series:
        cod = s["localidade"]["id"]
        for ano_str, pop_str in s["serie"].items():
            try:
                pop = int(pop_str)
            except (TypeError, ValueError):
                continue
            out[(cod, int(ano_str))] = pop
    return out


def load_uf_gold():
    """{(Ano, uf): {n_benef, valor_nominal, valor_2021, populacao_uf}}"""
    rows = json.loads(GOLD_UF.read_text(encoding="utf-8"))
    out = {}
    for r in rows:
        key = (r["Ano"], r["uf"])
        out[key] = {
            "n_benef":      r["n_benef"],
            "valor_nominal": r["valor_nominal"],
            "valor_2021":    r["valor_2021"],
            "populacao":     r["populacao"],
        }
    return out


def load_munis():
    """Lista de munis com pop, idhm, pobreza."""
    munis = []
    with REF_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            munis.append({
                "cod_municipio":     r["cod_municipio"],
                "municipio":         r["municipio"],
                "uf":                r["uf"],
                "regiao":            r["regiao"],
                "lat":               float(r["lat"]),
                "lon":               float(r["lon"]),
                "populacao_2022":    int(r["populacao_2022"]),
                "idhm_2010":         float(r["idhm_2010"]),
                "linha_pobreza_2010":float(r["linha_pobreza_2010"]),
            })
    return munis


def linear_pop_fallback(pop_2022: int, year: int) -> int:
    """Aproximação 1ª ordem (usada APENAS quando SIDRA não retornou aquele ano
    pra um muni — bem raro, ex: ano > último censo publicado). IBGE estimativa
    nacional: ~0.7% a.a. 2010-2022."""
    delta = (year - 2022) * 0.007
    return int(pop_2022 * (1 + delta))


def main() -> None:
    uf_gold = load_uf_gold()
    munis_all = load_munis()
    pop_serie = load_pop_muni_serie() or {}

    # Agrupar munis por UF
    munis_by_uf = defaultdict(list)
    for m in munis_all:
        munis_by_uf[m["uf"]].append(m)

    records = []
    skipped_keys = []
    for (year, uf), uf_data in uf_gold.items():
        munis_uf = munis_by_uf.get(uf, [])
        if not munis_uf:
            skipped_keys.append((year, uf))
            continue

        # População real IBGE/SIDRA quando disponível; fallback linear para
        # munis/anos não retornados pela SIDRA (raro).
        pop_y = {}
        for m in munis_uf:
            cod = m["cod_municipio"]
            real = pop_serie.get((cod, year))
            pop_y[cod] = real if real else linear_pop_fallback(m["populacao_2022"], year)
        # Peso de alocação: pop × pobreza
        weights = {m["cod_municipio"]: pop_y[m["cod_municipio"]] * m["linha_pobreza_2010"]
                   for m in munis_uf}
        w_total = sum(weights.values())
        if w_total <= 0:
            continue

        # Total da UF a ser alocado entre os munis da amostra. ATENÇÃO: a amostra
        # cobre apenas N munis da UF; a alocação aqui não conserva o total UF
        # (representaria distorção). Usamos como TOTAL a fração que corresponde
        # à fração populacional da amostra na UF — assim os totais por UF da
        # amostra somam ao "esperado" no subset, deixando o resto pra os ~5500
        # munis fora da amostra.
        pop_amostra_uf = sum(pop_y.values())
        # populacao UF do gold é o denominador real do per capita UF
        # populacao amostra = pop_amostra_uf
        share_amostra = pop_amostra_uf / max(uf_data["populacao"], 1)

        valor_nom_uf  = uf_data["valor_nominal"] * 1e3   # R$ bi → R$ mi
        valor_2021_uf = uf_data["valor_2021"]    * 1e3
        n_benef_uf    = uf_data["n_benef"]

        for m in munis_uf:
            cod = m["cod_municipio"]
            w = weights[cod] / w_total
            # Aloca-se a porção da amostra (share_amostra · w_total = share_amostra)
            # ponderada por w (intra-amostra)
            valor_nom = valor_nom_uf * share_amostra * w
            valor_2021 = valor_2021_uf * share_amostra * w
            n_benef    = int(n_benef_uf * share_amostra * w)
            pop_m      = pop_y[cod]
            per_benef  = (valor_2021 * 1e6) / n_benef if n_benef else 0
            per_capita = (valor_2021 * 1e6) / pop_m if pop_m else 0
            records.append({
                "Ano":           year,
                "cod_municipio": cod,
                "municipio":     m["municipio"],
                "uf":            uf,
                "regiao":        m["regiao"],
                "lat":           m["lat"],
                "lon":           m["lon"],
                "populacao":     pop_m,
                "n_benef":       n_benef,
                "valor_nominal": round(valor_nom, 4),
                "valor_2021":    round(valor_2021, 4),
                "pbfPerBenef":   round(per_benef, 2),
                "pbfPerCapita":  round(per_capita, 2),
                "idhm_2010":     m["idhm_2010"],
                "linha_pobreza_2010": m["linha_pobreza_2010"],
                "_source":       "fallback",
            })

    records.sort(key=lambda r: (r["Ano"], r["cod_municipio"]))

    OUT_JSON.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    n_munis = len({r["cod_municipio"] for r in records})
    n_anos  = len({r["Ano"] for r in records})
    print(f"✔ {OUT_JSON.relative_to(ROOT)}")
    print(f"  {len(records):,} linhas  ·  {n_munis} munis  ·  {n_anos} anos")
    print(f"  bytes={OUT_JSON.stat().st_size:,}")
    if skipped_keys:
        print(f"  ⚠ {len(skipped_keys)} keys (Ano, UF) sem munis na amostra")

    # ─── DQ check: alocação preserva conservação per capita por UF ─────────
    by_uf_year = defaultdict(lambda: {"valor": 0, "pop": 0})
    for r in records:
        k = (r["Ano"], r["uf"])
        by_uf_year[k]["valor"] += r["valor_2021"]
        by_uf_year[k]["pop"]   += r["populacao"]

    print("\n  Sanity check: per capita amostra vs UF oficial (1 ano, 3 UFs)")
    print(f"  {'UF':<3} {'Ano':<5} {'amostra_pc':>12} {'uf_pc':>12} {'razao':>6}")
    for uf in ["MA", "SP", "SC"]:
        for year in [2018, 2024]:
            ms = by_uf_year.get((year, uf))
            uf_d = uf_gold.get((year, uf))
            if ms and uf_d and ms["pop"] and uf_d["populacao"]:
                pc_amostra = (ms["valor"] * 1e6) / ms["pop"]
                pc_uf      = (uf_d["valor_2021"] * 1e9) / uf_d["populacao"]
                ratio = pc_amostra / pc_uf if pc_uf else 0
                print(f"  {uf:<3} {year:<5} {pc_amostra:>12,.2f} {pc_uf:>12,.2f} {ratio:>6.3f}")


if __name__ == "__main__":
    main()
