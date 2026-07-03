"""Correlações entre status curricular do cálculo e desempenho no PISA 2022.

Reprodutível (atende à cadeira de Finanças, R2): o achado central do artigo
sobre associação currículo x PISA passa a ter script correspondente, no mesmo
padrão de auditabilidade de audit_curricula_keywords.py.

Codificação ordinal do status do cálculo na trilha acadêmica/STEM:
  2 = compulsório para todos os estudantes da trilha (sem opção de saída);
  1 = eletivo / escolha de trilha avançada, típica de candidatos a STEM;
  0 = ausente do currículo nacional.

Convenção conservadora e explícita: só recebem 2 os sistemas em que o cálculo
integra a matemática compulsória de uma trilha científica (Alemanha, Itália,
Espanha, Rússia). Sistemas em que o cálculo está numa disciplina/opção
eletiva escolhida pelo estudante (Singapura H2, Japão Math III, França
Spécialité, Reino Unido A-Level etc.) recebem 1 --- ainda que, na prática,
seja a escolha default de quem pretende engenharia. O Brasil recebe 0.

Uso: conda activate dev-env; python scripts/compute_pisa_correlations.py
Determinístico (seed fixa). Dependências: numpy, scipy (ver requirements-audit.txt).
"""
from __future__ import annotations
import numpy as np
from scipy import stats

# (país, status ordinal, PISA 2022 matemática). IB excluído (sem PISA).
DATA = [
    ("Singapura",       1, 575),
    ("Japão",           1, 536),
    ("Coreia do Sul",   1, 527),
    ("Canadá",          1, 497),
    ("Reino Unido",     1, 489),
    ("Austrália",       1, 487),
    ("Finlândia",       1, 484),
    ("Rússia",          2, 478),
    ("Alemanha",        2, 475),
    ("França",          1, 474),
    ("Espanha",         2, 473),
    ("Itália",          2, 471),
    ("Estados Unidos",  1, 465),
    ("Israel",          1, 458),
    ("Brasil",          0, 379),
]

SEED = 20260703
N_BOOT = 10000
N_PERM = 20000


def main() -> None:
    rng = np.random.default_rng(SEED)
    status = np.array([d[1] for d in DATA])
    pisa = np.array([d[2] for d in DATA])
    n = len(DATA)

    rho = stats.spearmanr(status, pisa).statistic
    boots = []
    for _ in range(N_BOOT):
        idx = rng.integers(0, n, n)
        if len(set(status[idx])) < 2:
            continue
        boots.append(stats.spearmanr(status[idx], pisa[idx]).statistic)
    lo, hi = np.percentile(boots, [2.5, 97.5])

    obs = rho
    ge = sum(1 for _ in range(N_PERM)
             if stats.spearmanr(rng.permutation(status), pisa).statistic >= obs)
    p_perm = (ge + 1) / (N_PERM + 1)

    present = pisa[status > 0]
    z_brasil = (379 - present.mean()) / present.std(ddof=1)
    binp = (status > 0).astype(int)
    r_pb, p_pb = stats.pointbiserialr(binp, pisa)

    print(f"n = {n} (IB excluído: sem PISA)")
    print(f"Spearman rho (status ordinal x PISA 2022) = {rho:.2f}")
    print(f"  bootstrap 95% CI = [{lo:.2f}, {hi:.2f}]  (n_boot={len(boots)}, seed={SEED})")
    print(f"  permutation one-sided p = {p_perm:.3f}")
    print(f"Brasil: PISA=379; média dos presentes = {present.mean():.0f} "
          f"(dp {present.std(ddof=1):.0f}); z_Brasil = {z_brasil:.2f}")
    print(f"Point-biserial (ausente vs presente) r = {r_pb:.2f}  p = {p_pb:.3f}")
    print("Nota: com Brasil como único grupo 'ausente' (n=1), o r ponto-bisserial "
          "é uma reparametrização do z-score, não uma segunda evidência independente.")


if __name__ == "__main__":
    main()
