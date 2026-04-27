"""DQ tests para gold_pbf_estados_df.json.

Invariantes que o pipeline silver→gold DEVE garantir após o tratamento
do swap nov/2021 PBF→AB e a síntese PBF_AUX_SUM em
silver/pbf_total_uf_mes.py. Usado tanto em CI (GH Actions) quanto
localmente após qualquer refresh do gold.

Schema canonical: Ano, uf, n_benef, valor_nominal, valor_2021,
populacao, pbfPerBenef, pbfPerCapita.
"""
from collections import defaultdict


def test_row_count_in_expected_range(pbf_gold):
    """Gold deve ter ~350-400 rows (27 UFs × 13-14 anos completos)."""
    n = len(pbf_gold)
    assert 300 <= n <= 450, f"Row count fora da faixa esperada: {n:,}"


def test_all_27_ufs_present(pbf_gold, ufs_canonical):
    """Todas as 27 UFs brasileiras devem aparecer no gold."""
    ufs_in_gold = sorted({r['uf'] for r in pbf_gold})
    assert ufs_in_gold == ufs_canonical, \
        f"UFs faltando: {set(ufs_canonical) - set(ufs_in_gold)}"


def test_year_range(pbf_gold):
    """Gold deve cobrir 2013 até pelo menos 2024 (último ano completo)."""
    years = sorted({r['Ano'] for r in pbf_gold})
    assert min(years) == 2013, f"Primeiro ano deve ser 2013, é {min(years)}"
    assert max(years) >= 2024, f"Último ano deve ser >= 2024, é {max(years)}"


def test_schema_required_fields(pbf_gold):
    """Schema canonical deve incluir n_benef + ambos valores (nominal e real)."""
    required = {
        'Ano', 'uf', 'n_benef', 'valor_nominal', 'valor_2021',
        'populacao', 'pbfPerBenef', 'pbfPerCapita',
    }
    sample = pbf_gold[0]
    missing = required - set(sample.keys())
    assert not missing, f"Schema fields faltando: {missing}"


def test_n_benef_plausible_per_year(pbf_gold):
    """Soma nacional de n_benef por ano deve estar em 12M-26M.

    Faixa derivada da literatura: PBF clássico atendia 14-17M famílias;
    Auxílio Brasil saltou para ~24M; Novo Bolsa Família consolidou em
    22-23M. Anos parciais (em curso) ficam abaixo da faixa e são filtrados
    pelo gold (vide pbf_estados_df.py — n_months == 12).
    """
    by_year = defaultdict(int)
    for r in pbf_gold:
        by_year[r['Ano']] += r['n_benef']
    # 2026 pode estar em curso e cair fora — só checar anos de 2013 a 2025
    for year, n in sorted(by_year.items()):
        if year < 2013 or year > 2025:
            continue
        assert 12_000_000 <= n <= 27_000_000, \
            f"n_benef Brasil {year} fora da faixa 12M-27M: {n:,}"


def test_valor_2021_plausible_per_year(pbf_gold):
    """Soma nacional de valor_2021 (R$ bi) deve estar em 25-160 por ano.

    Faixa: PBF clássico ~36 bi, Auxílio Brasil ~65 bi, NBF ~130-141 bi.
    Em valores reais (deflacionados para dez/2021).
    """
    by_year = defaultdict(float)
    for r in pbf_gold:
        by_year[r['Ano']] += r['valor_2021']
    for year, v in sorted(by_year.items()):
        if year < 2013 or year > 2025:
            continue
        assert 25 <= v <= 160, \
            f"valor_2021 Brasil {year} fora da faixa R$ 25-160 bi: R$ {v:.1f} bi"


def test_per_capita_nordeste_higher_than_sul(pbf_gold):
    """Invariante substantiva: per capita Nordeste > Sul, todo ano.

    Critério de focalização do programa garante que UFs com maior
    pobreza monetária recebam mais por habitante. Quebra desse
    invariante indica bug no pipeline ou outlier sério a investigar.
    """
    NE = {'AL', 'BA', 'CE', 'MA', 'PB', 'PE', 'PI', 'RN', 'SE'}
    SUL = {'PR', 'RS', 'SC'}
    by_year_region = defaultdict(lambda: defaultdict(list))
    for r in pbf_gold:
        if r['uf'] in NE:
            by_year_region[r['Ano']]['NE'].append(r['pbfPerCapita'])
        elif r['uf'] in SUL:
            by_year_region[r['Ano']]['SUL'].append(r['pbfPerCapita'])
    for year, regions in sorted(by_year_region.items()):
        if year < 2013 or year > 2025:
            continue
        ne_mean = sum(regions['NE']) / len(regions['NE'])
        sul_mean = sum(regions['SUL']) / len(regions['SUL'])
        assert ne_mean > sul_mean, \
            f"{year}: per capita NE ({ne_mean:.0f}) <= Sul ({sul_mean:.0f}) — quebra de invariante de focalização"


def test_no_nulls_in_required_fields(pbf_gold):
    """Campos obrigatórios não podem ter null/None — gold deve ser dense."""
    required_non_null = ['Ano', 'uf', 'n_benef', 'valor_2021', 'populacao']
    for i, r in enumerate(pbf_gold):
        for f in required_non_null:
            assert r.get(f) is not None, \
                f"Row {i} (UF={r.get('uf')}, Ano={r.get('Ano')}) — campo {f} é null"


def test_per_benef_consistency(pbf_gold):
    """pbfPerBenef deve ser consistente com valor_2021 / n_benef × 1e9.

    Tolerância de 1% por arredondamentos. Se quebrar, há
    desalinhamento entre as agregações silver e gold.
    """
    for r in pbf_gold:
        if r['n_benef'] == 0:
            continue
        expected = r['valor_2021'] * 1e9 / r['n_benef']
        actual = r['pbfPerBenef']
        rel_err = abs(actual - expected) / expected if expected else 0
        assert rel_err < 0.01, \
            f"UF={r['uf']} Ano={r['Ano']}: pbfPerBenef={actual:.2f} ≠ valor_2021×1e9/n_benef={expected:.2f} (err {rel_err*100:.2f}%)"


def test_regime_jump_2021_to_2023(pbf_gold):
    """Invariante histórica: valor real nacional 2023 > 2× valor 2021.

    Documenta o salto Auxílio Brasil → Novo Bolsa Família. Se o pipeline
    silver erroneamente filtrar uma das origens (PBF/AUX/NBF), esse
    invariante quebra. ~R$ 30 bi (2021) → ~R$ 136 bi (2023) ≈ 4,5×.
    """
    by_year = defaultdict(float)
    for r in pbf_gold:
        by_year[r['Ano']] += r['valor_2021']
    v2021 = by_year[2021]
    v2023 = by_year[2023]
    assert v2023 > 2.0 * v2021, \
        f"2023 (R$ {v2023:.1f} bi) deveria ser > 2× 2021 (R$ {v2021:.1f} bi)"


def test_populacao_monotonic_per_uf(pbf_gold):
    """População por UF não deve cair >5% ano-a-ano.

    Detecta erros de merge com IBGE (population.json) que causariam
    distorção em pbfPerCapita. Aceita pequenas correções pós-Censo.
    """
    by_uf = defaultdict(dict)
    for r in pbf_gold:
        by_uf[r['uf']][r['Ano']] = r['populacao']
    for uf, years_pop in by_uf.items():
        years_sorted = sorted(years_pop.keys())
        for i in range(1, len(years_sorted)):
            prev = years_pop[years_sorted[i-1]]
            curr = years_pop[years_sorted[i]]
            if prev == 0:
                continue
            delta = (curr - prev) / prev
            assert delta > -0.05, \
                f"UF={uf} pop {years_sorted[i-1]}→{years_sorted[i]}: {prev:,}→{curr:,} ({delta*100:.1f}%)"
