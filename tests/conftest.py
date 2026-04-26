"""Pytest config + fixtures for Mirante data quality tests.

Tests rodam contra os JSONs de gold versionados em data/gold/. Não há
dependência em Spark/Databricks — testes são puramente em-memória sobre
os artefatos publicados, viabilizando CI rápido em GitHub Actions.
"""
import json
from pathlib import Path
import pytest

REPO = Path(__file__).resolve().parent.parent
GOLD_DIR = REPO / "data" / "gold"


@pytest.fixture(scope="session")
def equipamentos_gold():
    return json.load(open(GOLD_DIR / "gold_equipamentos_estados_ano.json"))


@pytest.fixture(scope="session")
def pbf_gold():
    return json.load(open(GOLD_DIR / "gold_pbf_estados_df.json"))


@pytest.fixture(scope="session")
def emendas_gold():
    return json.load(open(GOLD_DIR / "gold_emendas_estados_df.json"))


@pytest.fixture(scope="session")
def uropro_gold():
    return json.load(open(GOLD_DIR / "gold_uropro_estados_ano.json"))


@pytest.fixture(scope="session")
def rais_gold():
    p = GOLD_DIR / "gold_rais_estados_ano.json"
    return json.load(open(p)) if p.exists() else []


# Lista canonical de UFs brasileiras
UFS_BR = sorted([
    "AC","AL","AM","AP","BA","CE","DF","ES","GO","MA","MG","MS","MT",
    "PA","PB","PE","PI","PR","RJ","RN","RO","RR","RS","SC","SE","SP","TO",
])


@pytest.fixture(scope="session")
def ufs_canonical():
    return UFS_BR
