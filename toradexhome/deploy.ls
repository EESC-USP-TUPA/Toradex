#!/bin/bash

# ===============================
# CONFIGURAÇÕES
# ===============================

PROJECT_DIR="/home/torizon"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BRANCH="main"

echo "====================================="
echo "🚀 INICIANDO DEPLOY AUTOMÁTICO"
echo "====================================="

cd $PROJECT_DIR || exit 1

# ===============================
# GIT ADD
# ===============================
echo "📂 Adicionando arquivos..."
git add .

# ===============================
# GIT COMMIT
# ===============================
COMMIT_MSG="Auto deploy: $(date '+%Y-%m-%d %H:%M:%S')"

echo "📝 Commitando..."
git commit -m "$COMMIT_MSG"

# ===============================
# GIT PUSH
# ===============================
echo "☁️ Enviando para GitHub..."
git push origin $BRANCH

# ===============================
# DOCKER REBUILD
# ===============================
echo "🐳 Rebuildando Docker..."
docker compose -f $DOCKER_COMPOSE_FILE down
docker compose -f $DOCKER_COMPOSE_FILE build --no-cache
docker compose -f $DOCKER_COMPOSE_FILE up -d

echo "====================================="
echo "✅ DEPLOY FINALIZADO COM SUCESSO"
echo "====================================="
