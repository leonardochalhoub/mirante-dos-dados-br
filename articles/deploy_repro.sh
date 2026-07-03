#!/usr/bin/env bash
# Deploy do pacote de reprodutibilidade (articles/calculo-repro) para um repo
# público no GitHub, SEM materializar o token no disco nem no repositório.
#
# O token é lido de uma variável de ambiente ($GITHUB_TOKEN) em tempo de
# execução — nunca é escrito em arquivo, nunca é commitado.
#
# Uso:
#   export GITHUB_TOKEN=ghp_xxx           # cole aqui seu Personal Access Token (escopo: repo)
#   export REPO_NAME=calculo-ausente-repro   # opcional (nome neutro do repo)
#   bash articles/deploy_repro.sh
#
# Anonimato (revisão cega): o repo é criado sob a conta dona do token. Se essa
# conta revela seu nome, use um dos caminhos abaixo para a versão CEGA:
#   (a) submeta a URL do repo a https://anonymous.4open.science  -> link anônimo;
#   (b) crie o repo sob uma conta/organização de nome neutro;
#   (c) publique no OSF (osf.io) e gere um "view-only anonymized link".
# A URL real do GitHub entra apenas no camera-ready (após o aceite).
set -euo pipefail

: "${GITHUB_TOKEN:?defina GITHUB_TOKEN no ambiente (export GITHUB_TOKEN=...)}"
REPO_NAME="${REPO_NAME:-calculo-ausente-repro}"
SRC="$(cd "$(dirname "$0")" && pwd)/calculo-repro"
[ -d "$SRC" ] || { echo "bundle não encontrado: $SRC"; exit 1; }

# quem é o dono do token?
OWNER="$(curl -fsS -H "Authorization: token ${GITHUB_TOKEN}" https://api.github.com/user | grep -oE '"login": *"[^"]+"' | head -1 | sed -E 's/.*"login": *"([^"]+)".*/\1/')"
echo "Token pertence a: ${OWNER}"

# cria o repo (idempotente: ignora erro se já existir)
curl -fsS -X POST -H "Authorization: token ${GITHUB_TOKEN}" \
  https://api.github.com/user/repos \
  -d "{\"name\":\"${REPO_NAME}\",\"description\":\"O Cálculo Ausente — reproducibility package\",\"private\":false,\"has_issues\":false,\"has_wiki\":false}" \
  >/dev/null 2>&1 || echo "(repo já existe ou aviso ignorado)"

# publica a partir de uma cópia temporária (evita repo git aninhado no monorepo)
TMP="$(mktemp -d)"
cp -r "$SRC"/. "$TMP"/
cd "$TMP"
git init -q -b main
git add .
git -c user.name="Anonymous" -c user.email="anon@example.com" commit -q -m "O Cálculo Ausente — reproducibility package"
git remote add origin "https://${GITHUB_TOKEN}@github.com/${OWNER}/${REPO_NAME}.git"
git push -q -u origin main --force
cd - >/dev/null
rm -rf "$TMP"

echo
echo "✅ Publicado: https://github.com/${OWNER}/${REPO_NAME}"
echo "   Para a versão CEGA, gere um espelho anônimo em https://anonymous.4open.science"
