import server

print("########## LEDGER: RJ 2025 total ##########")
q1 = """
    SELECT uf, Ano, n_benef, valor_nominal, valor_2021, populacao, pbfPerBenef, pbfPerCapita
    FROM mirante_prd.gold.pbf_estados_df
    WHERE uf = 'RJ' AND Ano = 2025
"""
print(q1)
print(server.query_ledger(q1))

print("\n########## LEDGER: RJ série 2016-2025 (valor + populacao) ##########")
q2 = """
    SELECT Ano, valor_nominal, valor_2021, populacao, n_benef, pbfPerCapita
    FROM mirante_prd.gold.pbf_estados_df
    WHERE uf = 'RJ' AND Ano BETWEEN 2016 AND 2025
    ORDER BY Ano
"""
print(q2)
print(server.query_ledger(q2))

print("\n########## LEDGER: crescimento % população vs valor_2021, 2016->2025 ##########")
q3 = """
    WITH base AS (
      SELECT Ano, valor_2021, populacao
      FROM mirante_prd.gold.pbf_estados_df
      WHERE uf = 'RJ' AND Ano IN (2016, 2025)
    )
    SELECT * FROM base ORDER BY Ano
"""
print(q3)
print(server.query_ledger(q3))

print("\n########## MEMORY: metodologia (tecnologia/métodos usados) ##########")
print(server.search_memory("metodologia deflação IPCA agregação pipeline PBF Databricks Spark Delta", k=3))
