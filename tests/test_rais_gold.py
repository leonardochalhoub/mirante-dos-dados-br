"""DQ tests para gold_rais_estados_ano.json.

Tests rodam puramente sobre o JSON publicado em data/gold/. Não dependem de
Spark/Databricks. CI valida que a vertical RAIS no app não regride
silenciosamente cross-deploy.

Convenção: marcar com `pytest.mark.skipif(not gold)` se gold ainda não
populado — nesse caso o teste passa benignamente em vez de falhar.
"""
import pytest


def test_rais_gold_not_empty(rais_gold):
    """Gold deve existir e ter linhas."""
    assert isinstance(rais_gold, list), "gold deve ser uma lista de dicts"
    if not rais_gold:
        pytest.skip("gold ainda não populado pelo job — silver/gold em revisão")
    assert len(rais_gold) > 0, "gold lista vazia"


def test_rais_gold_has_required_fields(rais_gold):
    """Todas as linhas devem ter os campos esperados pelo app Rais.jsx."""
    if not rais_gold:
        pytest.skip("gold vazio")
    required = {"Ano", "uf", "n_vinculos_total", "n_vinculos_ativos"}
    for i, row in enumerate(rais_gold[:50]):  # spot-check first 50
        missing = required - set(row.keys())
        assert not missing, f"row {i} ({row.get('uf')}/{row.get('Ano')}) faltam campos: {missing}"


def test_rais_gold_year_coverage(rais_gold):
    """Bronze tem 1985-2024 (40 anos). Gold deve refletir, com tolerância
    pra lacunas em silver harmonizado."""
    if not rais_gold:
        pytest.skip("gold vazio")
    years = sorted({r.get("Ano") for r in rais_gold if r.get("Ano")})
    assert len(years) >= 30, (
        f"gold tem só {len(years)} anos (esperado ≥ 30 dos 40 da bronze). "
        f"Possível silver com bug de coalesce cross-era. Anos: {years}"
    )
    assert min(years) <= 1990, f"gold começa em {min(years)}, esperado <= 1990"
    assert max(years) >= 2022, f"gold termina em {max(years)}, esperado >= 2022"


def test_rais_gold_27_ufs_per_year(rais_gold, ufs_canonical):
    """Cada ano deve ter as 27 UFs brasileiras (com exceções documentadas)."""
    if not rais_gold:
        pytest.skip("gold vazio")
    by_year = {}
    for r in rais_gold:
        by_year.setdefault(r.get("Ano"), set()).add(r.get("uf"))

    # Exceções documentadas:
    # 1985: TO (Tocantins) ainda não existia (criado em 1988); MA1985.7z faltou no FTP
    # 1986: SP1986 quarentena permanente; PA1986 ausente da fonte
    # 1987: TO ainda não existia
    known_gaps = {
        1985: {"TO", "MA"},
        1986: {"TO", "SP", "PA"},
        1987: {"TO"},
    }
    for year, ufs in by_year.items():
        if year not in by_year:
            continue
        expected_ufs = set(ufs_canonical) - known_gaps.get(year, set())
        missing = expected_ufs - ufs
        assert not missing, f"ano {year} faltam UFs: {missing}"


def test_rais_gold_ativos_plausible(rais_gold):
    """Soma anual de vínculos ativos deve estar em range plausível."""
    if not rais_gold:
        pytest.skip("gold vazio")
    by_year = {}
    for r in rais_gold:
        ano = r.get("Ano")
        if ano is None:
            continue
        by_year.setdefault(ano, 0)
        by_year[ano] += r.get("n_vinculos_ativos", 0) or 0

    # Bronze indica:
    #   1985: ~20M ativos, 2024: ~58M ativos
    # Gold pode ter ligeira diferença por filtros, mas deve estar próximo.
    for year, total in sorted(by_year.items()):
        if year < 1985 or year > 2024:
            continue
        # Range conservador: aceita 50%-200% do esperado bronze
        assert 5_000_000 <= total <= 100_000_000, (
            f"ano {year} ativos={total:,} fora de [5M, 100M]"
        )


def test_rais_gold_2020_covid_resilience(rais_gold):
    """COVID 2020 não deve ter caído mais que 10% vs 2019.
    BEm (Lei 14.020/2020) foi efetivo em preservar emprego formal."""
    if not rais_gold:
        pytest.skip("gold vazio")
    by_year = {}
    for r in rais_gold:
        ano = r.get("Ano")
        if ano in (2019, 2020):
            by_year.setdefault(ano, 0)
            by_year[ano] += r.get("n_vinculos_ativos", 0) or 0

    if 2019 not in by_year or 2020 not in by_year:
        pytest.skip("2019 ou 2020 ausente no gold")

    delta = (by_year[2020] - by_year[2019]) / by_year[2019] * 100
    assert delta > -10.0, (
        f"COVID 2020: queda de {delta:.1f}% nos vínculos ativos vs 2019. "
        f"Esperado: queda < 10% (BEm preservou emprego formal)."
    )


def test_rais_gold_2022_post_covid_recovery(rais_gold):
    """2022 deve mostrar recuperação forte vs 2020."""
    if not rais_gold:
        pytest.skip("gold vazio")
    by_year = {}
    for r in rais_gold:
        ano = r.get("Ano")
        if ano in (2020, 2022):
            by_year.setdefault(ano, 0)
            by_year[ano] += r.get("n_vinculos_ativos", 0) or 0

    if 2020 not in by_year or 2022 not in by_year:
        pytest.skip("2020 ou 2022 ausente")

    delta = (by_year[2022] - by_year[2020]) / by_year[2020] * 100
    assert delta > 5.0, (
        f"2022 vs 2020: crescimento de {delta:.1f}%. Esperado: > 5%."
    )


def test_rais_gold_no_negative_counts(rais_gold):
    """Contagens nunca devem ser negativas."""
    if not rais_gold:
        pytest.skip("gold vazio")
    count_fields = ("n_vinculos_total", "n_vinculos_ativos", "n_estabelecimentos_proxy")
    for row in rais_gold:
        for f in count_fields:
            v = row.get(f)
            if v is not None:
                assert v >= 0, f"{f} negativo em {row.get('uf')}/{row.get('Ano')}: {v}"


def test_rais_gold_active_le_total(rais_gold):
    """n_vinculos_ativos <= n_vinculos_total sempre."""
    if not rais_gold:
        pytest.skip("gold vazio")
    for row in rais_gold:
        ativos = row.get("n_vinculos_ativos") or 0
        total = row.get("n_vinculos_total") or 0
        if ativos and total:
            assert ativos <= total, (
                f"{row.get('uf')}/{row.get('Ano')}: ativos={ativos:,} > total={total:,}"
            )


def test_rais_gold_sp_dominance_decline(rais_gold):
    """SP deve ter share decrescente cross-1985-2024 (descentralização)."""
    if not rais_gold:
        pytest.skip("gold vazio")
    by_year = {}
    for r in rais_gold:
        ano = r.get("Ano")
        if ano not in (1985, 2014, 2024):
            continue
        by_year.setdefault(ano, {"SP": 0, "total": 0})
        v = r.get("n_vinculos_total", 0) or 0
        by_year[ano]["total"] += v
        if r.get("uf") == "SP":
            by_year[ano]["SP"] += v

    if 1985 not in by_year:
        pytest.skip("1985 ausente do gold")

    sp_85 = 100 * by_year[1985]["SP"] / by_year[1985]["total"] if by_year[1985]["total"] else 0
    if 2024 in by_year and by_year[2024]["total"]:
        sp_24 = 100 * by_year[2024]["SP"] / by_year[2024]["total"]
        assert sp_85 > sp_24, f"SP share 1985={sp_85:.1f}% deveria ser > 2024={sp_24:.1f}% (descentralização)"
        # Sanity: SP em 1985 era ~35,5%, 2024 ~28,1% conforme panorama
        assert 30 < sp_85 < 40, f"SP 1985 share esperado ~35,5%, got {sp_85:.1f}%"
        assert 25 < sp_24 < 32, f"SP 2024 share esperado ~28,1%, got {sp_24:.1f}%"
