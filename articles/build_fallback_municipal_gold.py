#!/usr/bin/env python3
"""Constrói fallback gold municipal para o WP#7 (Bolsa Família por Município).

CONTEXTO. Este script gera uma versão LOCAL e TRANSPARENTE do gold municipal
quando o pipeline completo de Databricks (silver/pbf_total_municipio_mes →
gold/pbf_municipios_df → export/pbf_municipios_df_json) ainda não rodou.

ENTRADAS (todas reais e públicas):
  1. data/gold/gold_pbf_estados_df.json — gold UF × Ano com totais reais (CGU)
  2. data/reference/ibge_municipios.csv — 5.571 munis IBGE Localidades v1 +
     centroides kelvins/Municipios-Brasileiros (cod_municipio, municipio, uf,
     regiao, lat, lon, capital).
  3. data/fallback/ibge_populacao_municipios.json — população real IBGE/SIDRA
     6579 (var 9324) por município × ano. Anos 2013-2021, 2024, 2025; 2022 e
     2023 (Censo years) extrapolados linearmente entre 2021 e 2024.

ALOCAÇÃO (transparente, não fabricada):
  Para cada (UF, Ano), distribuímos o total UF (do gold real) entre TODOS os
  munis da UF no IBGE, ponderando por w_uf,muni = pop_muni × pobreza_uf.
  Como pobreza_uf é uniforme dentro da UF (PNAD-C 2019), a alocação efetiva
  fica proporcional à população: w ≈ pop_muni · const_uf. Isso preserva
  EXATAMENTE o per capita da UF (sanity ratio = 1.000) — a heterogeneidade
  intra-UF que aparece nas figuras vem da variação populacional, não de
  diferenciais de focalização (que requerem o pipeline Databricks).

LIMITAÇÃO. O fallback NÃO captura heterogeneidade de focalização entre
munis dentro da mesma UF — para isso é necessário o pipeline Databricks
com microdados CGU agregados por município. Esta limitação está
explicitada no manuscrito.

SAÍDAS:
  data/fallback/gold_pbf_municipios_df.json
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLD_UF  = ROOT / "data" / "gold"      / "gold_pbf_estados_df.json"
REF_CSV  = ROOT / "data" / "reference" / "ibge_municipios.csv"
POP_MUN  = ROOT / "data" / "fallback"  / "ibge_populacao_municipios.json"
OUT_JSON = ROOT / "data" / "fallback"  / "gold_pbf_municipios_df.json"

# Pobreza UF — % pop com renda < linha pobreza, PNAD-C 2019. Mesma fonte
# do articles/causal_analysis_pbf.py (WP#2).
POBREZA_UF_2019 = {
    "AC": 36.4, "AL": 47.4, "AM": 41.7, "AP": 35.5, "BA": 38.2,
    "CE": 41.9, "DF": 12.4, "ES": 17.1, "GO": 17.9, "MA": 51.9,
    "MG": 19.7, "MS": 17.0, "MT": 19.3, "PA": 41.4, "PB": 43.5,
    "PE": 41.0, "PI": 47.5, "PR": 13.7, "RJ": 19.1, "RN": 39.4,
    "RO": 22.8, "RR": 38.1, "RS": 12.1, "SC":  9.8, "SE": 41.9,
    "SP": 13.8, "TO": 28.6,
}

# IDH-M UF (Atlas Brasil 2010 — média ponderada por população dos munis).
# Quando IDH-M municipal não estiver disponível, usar este valor como proxy.
IDHM_UF_2010 = {
    "AC": 0.663, "AL": 0.631, "AM": 0.674, "AP": 0.708, "BA": 0.660,
    "CE": 0.682, "DF": 0.824, "ES": 0.740, "GO": 0.735, "MA": 0.639,
    "MG": 0.731, "MS": 0.729, "MT": 0.725, "PA": 0.646, "PB": 0.658,
    "PE": 0.673, "PI": 0.646, "PR": 0.749, "RJ": 0.761, "RN": 0.684,
    "RO": 0.690, "RR": 0.707, "RS": 0.746, "SC": 0.774, "SE": 0.665,
    "SP": 0.783, "TO": 0.699,
}


def load_uf_gold():
    rows = json.loads(GOLD_UF.read_text(encoding="utf-8"))
    out = {}
    for r in rows:
        out[(r["Ano"], r["uf"])] = {
            "n_benef":      r["n_benef"],
            "valor_nominal": r["valor_nominal"],   # R$ bi
            "valor_2021":    r["valor_2021"],      # R$ bi
            "populacao":     r["populacao"],
        }
    return out


def load_munis():
    """Carrega 5.571 munis do reference CSV."""
    out = []
    with REF_CSV.open(encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["lat"] or not r["lon"]:
                continue
            out.append({
                "cod_municipio": r["cod_municipio"],
                "municipio":     r["municipio"],
                "uf":            r["uf"],
                "regiao":        r["regiao"],
                "lat":           float(r["lat"]),
                "lon":           float(r["lon"]),
                "capital":       int(r["capital"] or 0),
            })
    return out


def load_pop_serie():
    """Real IBGE/SIDRA: {(cod_muni, ano): populacao}.
    Anos 2022 e 2023 (Censo) são extrapolados linearmente entre 2021 e 2024."""
    if not POP_MUN.exists():
        print(f"⚠ {POP_MUN.relative_to(ROOT)} ausente — rode "
              f"articles/fetch_ibge_populacao_municipios.py primeiro.")
        return {}, []
    payload = json.loads(POP_MUN.read_text(encoding="utf-8"))
    series = payload[0]["resultados"][0]["series"]
    out = {}
    for s in series:
        cod = s["localidade"]["id"]
        for ano_str, pop_str in s["serie"].items():
            try:
                pop = int(pop_str) if pop_str and pop_str != "..." else None
            except (TypeError, ValueError):
                pop = None
            if pop:
                out[(cod, int(ano_str))] = pop

    # Extrapolação linear para anos sem publicação
    cods = {k[0] for k in out}
    years_seen = sorted({k[1] for k in out})
    years_target = list(range(min(years_seen), max(years_seen) + 1))
    n_extrap = 0
    for cod in cods:
        for y in years_target:
            if (cod, y) in out:
                continue
            # Buscar o ano antes e depois mais próximos com dado
            anterior = max((yy for yy in years_seen if yy < y and (cod, yy) in out), default=None)
            posterior = min((yy for yy in years_seen if yy > y and (cod, yy) in out), default=None)
            if anterior is None and posterior is None:
                continue
            if anterior is None:
                pop = out[(cod, posterior)]
            elif posterior is None:
                pop = out[(cod, anterior)]
            else:
                p_a = out[(cod, anterior)]
                p_b = out[(cod, posterior)]
                # interpolação linear
                t = (y - anterior) / (posterior - anterior)
                pop = int(p_a + t * (p_b - p_a))
            out[(cod, y)] = pop
            n_extrap += 1
    print(f"  pop_serie: {len(out):,} pares (cod, ano); {n_extrap:,} extrapolados linearmente")
    return out, years_target


def main() -> None:
    uf_gold = load_uf_gold()
    munis_all = load_munis()
    print(f"Munis carregados: {len(munis_all):,}")
    pop_serie, years_target = load_pop_serie()

    munis_by_uf = defaultdict(list)
    for m in munis_all:
        munis_by_uf[m["uf"]].append(m)
    print(f"Munis por UF: {dict((u, len(ms)) for u, ms in sorted(munis_by_uf.items()))}")

    records = []
    for (year, uf), uf_data in sorted(uf_gold.items()):
        if year not in years_target and not (year >= years_target[0] and year <= years_target[-1]):
            continue
        munis_uf = munis_by_uf.get(uf, [])
        if not munis_uf:
            continue

        pob_uf = POBREZA_UF_2019.get(uf, 25.0)  # fallback ~mediana
        idhm_uf = IDHM_UF_2010.get(uf, 0.700)

        # Pop por muni nesse ano
        pop_y = {}
        for m in munis_uf:
            cod = m["cod_municipio"]
            p = pop_serie.get((cod, year))
            if p:
                pop_y[cod] = p
        if not pop_y:
            continue

        # Peso = pop × pobreza_UF (pobreza uniforme dentro da UF)
        # Como pobreza_UF é uniforme, weight_relative = pop / pop_total_amostra
        pop_amostra = sum(pop_y.values())
        if pop_amostra <= 0:
            continue

        # Compatibilidade total UF: a pop_amostra (5570 munis no fallback)
        # deve ser ~ igual à uf_data["populacao"]; se houver mismatch (raro,
        # ex: extrapolação imperfeita), share_amostra ajusta para preservar
        # per_capita exatamente.
        share_amostra = pop_amostra / max(uf_data["populacao"], 1)
        valor_nom_uf  = uf_data["valor_nominal"] * 1e3   # bi → mi
        valor_2021_uf = uf_data["valor_2021"]    * 1e3
        n_benef_uf    = uf_data["n_benef"]

        for m in munis_uf:
            cod = m["cod_municipio"]
            if cod not in pop_y:
                continue
            w = pop_y[cod] / pop_amostra
            valor_nom = valor_nom_uf  * share_amostra * w
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
                "idhm_2010":     idhm_uf,         # UF-level proxy
                "linha_pobreza_2010": pob_uf,     # UF-level proxy
                "_source":       "fallback",
            })

    records.sort(key=lambda r: (r["Ano"], r["cod_municipio"]))
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    n_munis = len({r["cod_municipio"] for r in records})
    n_anos  = len({r["Ano"] for r in records})
    print(f"\n✔ {OUT_JSON.relative_to(ROOT)}")
    print(f"  {len(records):,} linhas  ·  {n_munis:,} munis  ·  {n_anos} anos")
    print(f"  bytes={OUT_JSON.stat().st_size:,}")

    # Sanity check
    by_uf_year = defaultdict(lambda: {"valor": 0, "pop": 0})
    for r in records:
        k = (r["Ano"], r["uf"])
        by_uf_year[k]["valor"] += r["valor_2021"]
        by_uf_year[k]["pop"]   += r["populacao"]

    print("\n  Sanity: per capita amostra vs UF oficial")
    print(f"  {'UF':<3} {'Ano':<5} {'amostra_pc':>12} {'uf_pc':>12} {'razao':>6}")
    for uf in ["MA", "SP", "SC", "DF"]:
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
