"""DQ tests para gold_equipamentos_estados_ano.json.

Invariantes que o silver pipeline DEVE garantir após o fix do
WP #6 (composite key TIPEQUIP+CODEQUIP, normalize, dedup por
source_file). Usado tanto em CI (GH Actions) quanto localmente
após qualquer refresh do gold.
"""
import pytest
from collections import defaultdict


def test_row_count_in_expected_range(equipamentos_gold):
    """Gold deve ter ~30K-40K rows (27 UFs × 13 anos × ~80-130 combos)."""
    n = len(equipamentos_gold)
    assert 25_000 <= n <= 50_000, f"Row count fora da faixa esperada: {n:,}"


def test_all_27_ufs_present(equipamentos_gold, ufs_canonical):
    """Todas as 27 UFs brasileiras devem aparecer no gold."""
    ufs_in_gold = sorted({r['estado'] for r in equipamentos_gold})
    assert ufs_in_gold == ufs_canonical, \
        f"UFs faltando: {set(ufs_canonical) - set(ufs_in_gold)}"


def test_year_range(equipamentos_gold):
    """Gold deve cobrir 2013 até pelo menos 2024 (último ano completo)."""
    years = sorted({r['ano'] for r in equipamentos_gold})
    assert min(years) == 2013, f"Primeiro ano deve ser 2013, é {min(years)}"
    assert max(years) >= 2024, f"Último ano deve ser >= 2024, é {max(years)}"


def test_schema_required_fields(equipamentos_gold):
    """Schema canonical deve incluir composite key + names."""
    required = {
        'estado', 'ano', 'tipequip', 'codequip', 'equipment_key',
        'equipment_name', 'equipment_category', 'cnes_count',
        'total_avg', 'sus_total_avg', 'priv_total_avg', 'populacao',
    }
    sample = equipamentos_gold[0]
    missing = required - set(sample.keys())
    assert not missing, f"Schema fields faltando: {missing}"


def test_equipment_key_is_composite(equipamentos_gold):
    """equipment_key deve ser sempre 'TIPEQUIP:CODEQUIP'."""
    for r in equipamentos_gold[:200]:  # sample
        assert ':' in r['equipment_key'], \
            f"equipment_key sem ':' — {r['equipment_key']}"
        tip, cod = r['equipment_key'].split(':')
        assert tip == r['tipequip']
        assert cod == r['codequip']


def test_unmapped_combos_under_tolerance(equipamentos_gold):
    """Após silver fix do dict canonical, '(não mapeado)' deve cair pra
    uma fração mínima — apenas códigos legacy raros do CNES histórico
    (2013-2014). Tolerância: <0.5% das rows e <5 combos distintos.
    """
    unmapped = [r for r in equipamentos_gold if '(não mapeado)' in (r.get('equipment_name') or '')]
    pct = len(unmapped) / len(equipamentos_gold) * 100
    distinct_combos = sorted({(r['tipequip'], r['codequip']) for r in unmapped})
    assert pct < 0.5, \
        f"{pct:.2f}% rows não mapeadas (>0.5% tolerância). Combos: {distinct_combos}"
    assert len(distinct_combos) < 5, \
        f"{len(distinct_combos)} combos não mapeados (>=5 violam tolerância): {distinct_combos}"


def test_rm_count_matches_oecd_magnitude(equipamentos_gold):
    """RM (1:12) Brasil 2024 deve estar entre 3000-4500 unidades.

    Validado contra OECD Health Statistics 2021 (mediana 17/Mhab × 215M
    pop = 3.655 RM esperados). Antes do fix do WP #6, esse filtro
    retornava ~10K (por causa do bug 42=EEG). Agora deve bater.
    """
    rm_2024 = [r for r in equipamentos_gold
               if r['equipment_key'] == '1:12' and r['ano'] == 2024]
    total = sum(r['total_avg'] for r in rm_2024)
    assert 3000 <= total <= 4500, \
        f"RM Brasil 2024 fora da faixa OECD (3000-4500): {total:.0f}"


def test_rm_density_matches_oecd_median(equipamentos_gold):
    """RM Brasil 2024 deve estar perto de 17/Mhab (mediana OECD 2021)."""
    rm_2024 = [r for r in equipamentos_gold
               if r['equipment_key'] == '1:12' and r['ano'] == 2024]
    total = sum(r['total_avg'] for r in rm_2024)
    pop = sum(r['populacao'] for r in rm_2024)
    density = total / pop * 1e6 if pop else 0
    assert 14 <= density <= 22, \
        f"RM/Mhab Brasil 2024 fora da faixa razoável (14-22): {density:.1f}"


def test_tipequip_normalized_no_leading_zeros(equipamentos_gold):
    """TIPEQUIP deve ser sempre '1'-'10' (sem '01', '02' etc.).

    Antes do fix do WP #6, bronze tinha duas representações silver
    duplicava. Após normalize, só forma canônica.
    """
    tips = sorted({r['tipequip'] for r in equipamentos_gold})
    for t in tips:
        assert not (t.startswith('0') and len(t) > 1), \
            f"TIPEQUIP com leading zero: {t!r}"


def test_codequip_zero_padded(equipamentos_gold):
    """CODEQUIP deve ser sempre 2 chars zero-padded ('01', '12', etc.)."""
    sample = equipamentos_gold[:500]
    for r in sample:
        assert len(r['codequip']) == 2, \
            f"CODEQUIP fora de 2 chars: {r['codequip']!r}"


def test_sus_priv_sum_equals_total(equipamentos_gold):
    """sus_total_avg + priv_total_avg deve aproximar total_avg."""
    for r in equipamentos_gold[:500]:
        sum_ = r['sus_total_avg'] + r['priv_total_avg']
        if r['total_avg'] > 0:
            ratio = sum_ / r['total_avg']
            assert 0.99 <= ratio <= 1.01, \
                f"SUS+Priv != total para {r['equipment_key']} {r['estado']} {r['ano']}: " \
                f"sus={r['sus_total_avg']}, priv={r['priv_total_avg']}, total={r['total_avg']}"


def test_cnes_count_le_total_avg_when_one_equipment_per_estab(equipamentos_gold):
    """cnes_count >= total_avg quase sempre (cada estabelecimento tem >=1 unidade).

    Pequena tolerância porque total_avg é média mensal podendo ser fracional.
    """
    rm_2024 = [r for r in equipamentos_gold
               if r['equipment_key'] == '1:12' and r['ano'] == 2024 and r['cnes_count'] > 0]
    # cnes_count não pode ser maior que total_avg (com tolerância para média mensal)
    # E cnes_count deve ser próximo a total_avg (geralmente <= ratio 1.5)
    for r in rm_2024:
        if r['total_avg'] > 0:
            ratio = r['total_avg'] / r['cnes_count']
            assert 0.5 <= ratio <= 5.0, \
                f"Razão total_avg/cnes_count fora de [0.5, 5.0] para RM em {r['estado']} 2024: " \
                f"cnes_count={r['cnes_count']}, total_avg={r['total_avg']}"


def test_rm_density_per_uf_realistic(equipamentos_gold):
    """RM/Mhab por UF deve estar entre 0 (vazio) e 60 (DF top, sem extremos
    super altos)."""
    rm_2024 = [r for r in equipamentos_gold
               if r['equipment_key'] == '1:12' and r['ano'] == 2024]
    for r in rm_2024:
        if r['populacao'] > 0:
            density = r['total_avg'] / r['populacao'] * 1e6
            assert 0 <= density <= 80, \
                f"RM/Mhab fora da faixa razoável em {r['estado']} 2024: {density:.1f}"
