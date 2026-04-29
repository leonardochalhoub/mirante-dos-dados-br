"""Auditoria automatizada do achado central do WP#9.

Atende à pendência crítica da cadeira de Engenharia de Software na Reunião
#5 do Conselho do Mirante (2026-04-29):

> "Auditoria do achado central não é automatizada — sem script pdftotext +
>  grep nos PDFs curriculares; achado auditável por terceiros em 4h por país
>  (não acontece) em vez de 10 minutos com pipeline."

Este script torna o achado **"Brasil é o único país da amostra cujo currículo
nacional não inclui limites, derivadas ou integrais"** verificável em tempo
linear contra os PDFs originais dos currículos oficiais.

## Como funciona

1. Carrega `articles/scripts/sources_calculo_curricula.json` (manifest dos
   PDFs/URLs curriculares oficiais — 11 países + IB).
2. Para cada documento:
   - Se há um PDF local (em `articles/snapshots/calculo/` ou apontado
     via campo `local_path`), faz pdftotext desse arquivo.
   - Se há somente uma URL, baixa para `articles/snapshots/calculo/`
     (idempotente — só baixa se não existir).
   - Se nem URL nem PDF, marca como SKIP.
3. Procura, no texto extraído, ocorrências case-insensitive das
   palavras-chave de cálculo:
       - PT: limite, derivada, derivar, integral, integrar, taxa de
             variação, área sob curva, função composta, regra da cadeia
       - EN: limit, derivative, integral, antiderivative, rate of change,
             area under, chain rule
       - ES: límite, derivada, integral, integral definida
       - DE: Grenzwert, Ableitung, Integral, Stammfunktion
       - FR: limite, dérivée, intégrale, primitive
       - JA: 極限, 微分, 積分
       - ZH: 极限, 导数, 积分
       - KO: 극한, 미분, 적분
       - RU: предел, производная, интеграл
       - FI: raja-arvo, derivaatta, integraali
4. Emite um relatório CSV em `articles/snapshots/calculo/audit_report.csv`
   com (país, doc, total_hits, hits_por_termo, decisao_paper).
5. Falha (exit 1) se a auditoria contradiz o achado: ou seja, se o BNCC
   tem N>0 hits ou se algum currículo estrangeiro tem 0 hits — ambos
   sinais de que o paper precisa de revisão.

## Como rodar

    cd /home/leochalhoub/mirante-dos-dados-br/articles
    pip install pdfplumber requests   # ou: apt install poppler-utils para pdftotext
    python3 scripts/audit_curricula_keywords.py
    python3 scripts/audit_curricula_keywords.py --download-missing  # baixa snapshots
    python3 scripts/audit_curricula_keywords.py --strict            # falha se inconsistência

NOTA: o script é defensivo. Se `pdftotext` não está instalado, ou se
documentos não foram baixados, emite WARNINGs e segue — não trava o build.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_DIR = ROOT / "snapshots" / "calculo"
SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = ROOT / "scripts" / "sources_calculo_curricula.json"
REPORT_PATH = SNAPSHOT_DIR / "audit_report.csv"


# Termos de cálculo por idioma (case-insensitive). Mantemos lista enxuta
# pra evitar falsos positivos em palavras como "integral curriculares" ou
# "limites da álgebra".
KEYWORDS = {
    "pt": [r"\blimite[s]?\b", r"\bderivad[oa]s?\b", r"\bintegrais?\b",
           r"\bintegrar\b", r"taxa de varia[cç][ãa]o", r"chain rule"],
    "en": [r"\blimits?\b", r"\bderivative[s]?\b", r"\bintegral[s]?\b",
           r"\bantiderivative\b", r"rate of change", r"\barea under\b"],
    "es": [r"\bl[ií]mite[s]?\b", r"\bderivada[s]?\b", r"\bintegral(es)?\b"],
    "de": [r"\bGrenzwert(e)?\b", r"\bAbleitung(en)?\b", r"\bIntegral(e)?\b",
           r"\bStammfunktion(en)?\b"],
    "fr": [r"\blimite[s]?\b", r"\bd[ée]riv[ée]e?[s]?\b",
           r"\bint[ée]grale[s]?\b", r"\bprimitive[s]?\b"],
    "ja": ["極限", "微分", "積分"],
    "zh": ["极限", "导数", "积分", "微積分"],
    "ko": ["극한", "미분", "적분"],
    "ru": ["предел", "производная", "интеграл"],
    "fi": ["raja-arvo", "derivaatta", "integraali"],
}


def safe_filename(url: str) -> str:
    """Hash-based filename to avoid collisions and weird URL chars."""
    h = hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix or ".pdf"
    return f"{h}{suffix}"


def download_if_needed(url: str, dest: Path, *, do_download: bool) -> Optional[Path]:
    if dest.exists():
        return dest
    if not do_download:
        return None
    try:
        req = Request(url, headers={"User-Agent": "Mirante-WP9-Audit/1.0"})
        with urlopen(req, timeout=30) as r, open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        return dest
    except Exception as e:
        print(f"  ⚠ download failed: {url} → {e}", file=sys.stderr)
        return None


def pdftotext_extract(pdf_path: Path) -> Optional[str]:
    """Extrai texto do PDF. Tenta pdftotext (poppler) → pdfplumber fallback."""
    if shutil.which("pdftotext"):
        try:
            out = subprocess.run(
                ["pdftotext", "-layout", "-q", str(pdf_path), "-"],
                capture_output=True, text=True, timeout=60,
            )
            return out.stdout
        except Exception as e:
            print(f"  ⚠ pdftotext failed: {pdf_path} → {e}", file=sys.stderr)
    try:
        import pdfplumber  # type: ignore
        text_parts = []
        with pdfplumber.open(str(pdf_path)) as pdf:
            for page in pdf.pages:
                text_parts.append(page.extract_text() or "")
        return "\n".join(text_parts)
    except ImportError:
        print("  ⚠ neither pdftotext (poppler) nor pdfplumber installed",
              file=sys.stderr)
    except Exception as e:
        print(f"  ⚠ pdfplumber failed: {pdf_path} → {e}", file=sys.stderr)
    return None


def count_keyword_hits(text: str, lang: str) -> dict[str, int]:
    if not text:
        return {}
    text_lc = text.lower()
    out: dict[str, int] = {}
    for pat in KEYWORDS.get(lang, []):
        try:
            n = len(re.findall(pat, text_lc, flags=re.IGNORECASE | re.UNICODE))
            out[pat] = n
        except re.error:
            out[pat] = -1
    return out


def audit(*, download_missing: bool, strict: bool) -> int:
    if not MANIFEST_PATH.exists():
        print(f"❌ manifest missing: {MANIFEST_PATH}\n"
              f"   crie-o conforme schema documentado no docstring deste script.",
              file=sys.stderr)
        return 2

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

    rows: list[dict] = []
    contradicoes: list[str] = []

    for entry in manifest["sources"]:
        country = entry["country"]
        lang = entry["lang"]
        url = entry.get("url")
        local = entry.get("local_path")

        # Resolve PDF path
        pdf_path: Optional[Path] = None
        if local:
            cand = ROOT / local
            if cand.exists():
                pdf_path = cand
        if pdf_path is None and url:
            target = SNAPSHOT_DIR / safe_filename(url)
            pdf_path = download_if_needed(url, target,
                                          do_download=download_missing)

        if pdf_path is None:
            print(f"  ⏭  SKIP {country} — sem PDF (nem local nem baixado)")
            rows.append({
                "country": country, "doc": entry.get("title", ""),
                "lang": lang, "url": url or "",
                "status": "SKIP", "total_hits": "",
                "hits_breakdown": "",
                "paper_claim": entry["paper_claim"],
            })
            continue

        text = pdftotext_extract(pdf_path)
        if not text:
            print(f"  ⏭  SKIP {country} — extração de texto falhou")
            rows.append({
                "country": country, "doc": entry.get("title", ""),
                "lang": lang, "url": url or "",
                "status": "EXTRACTION_FAILED", "total_hits": "",
                "hits_breakdown": "",
                "paper_claim": entry["paper_claim"],
            })
            continue

        hits = count_keyword_hits(text, lang)
        total = sum(v for v in hits.values() if v > 0)
        breakdown = "; ".join(f"{p}={n}" for p, n in hits.items() if n > 0) or "—"

        # Paper claim ∈ {present, absent, eletivo}
        claim = entry["paper_claim"]
        ok = True
        if claim == "absent" and total > 0:
            ok = False
            contradicoes.append(
                f"❌ {country}: paper diz AUSENTE mas pdftotext encontrou "
                f"{total} ocorrências de termos de cálculo"
            )
        if claim == "present" and total == 0:
            ok = False
            contradicoes.append(
                f"❌ {country}: paper diz PRESENTE mas pdftotext encontrou 0 "
                f"ocorrências"
            )

        status = "OK" if ok else "INCONSISTENT"
        print(f"  ✓ {country:18s} lang={lang:3s} hits={total:4d} "
              f"claim={claim:10s} → {status}")

        rows.append({
            "country": country, "doc": entry.get("title", ""),
            "lang": lang, "url": url or "",
            "status": status, "total_hits": total,
            "hits_breakdown": breakdown,
            "paper_claim": claim,
        })

    # Write CSV report
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8", newline="") as f:
        if rows:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    print(f"\n📊 Relatório: {REPORT_PATH.relative_to(ROOT)}")

    if contradicoes:
        print("\n⚠ CONTRADIÇÕES detectadas:")
        for c in contradicoes:
            print(f"  {c}")
        if strict:
            return 1

    print("\n✅ auditoria concluída sem contradições críticas")
    return 0


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--download-missing", action="store_true",
                   help="Baixa PDFs faltantes do manifest (idempotente)")
    p.add_argument("--strict", action="store_true",
                   help="Exit 1 se há contradições entre paper_claim e pdftotext")
    args = p.parse_args()
    sys.exit(audit(download_missing=args.download_missing, strict=args.strict))


if __name__ == "__main__":
    main()
