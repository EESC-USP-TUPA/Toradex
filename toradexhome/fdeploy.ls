#!/bin/bash

PROJECT_DIR="/home/torizon"
DOCKER_COMPOSE_FILE="docker-compose.yml"
BRANCH="main"

echo "🚀 Smart Deploy Starting..."

cd $PROJECT_DIR || exit 1

# =====================================
# GIT
# =====================================

git add .

if git diff --cached --quiet; then
    echo "🟢 No code changes detected."
else
    COMMIT_MSG="Auto deploy: $(date '+%Y-%m-%d %H:%M:%S')"
    git commit -m "$COMMIT_MSG"
    git push origin $BRANCH
fi

# =====================================
# DOCKER SMART BUILD
# =====================================

echo "🐳 Rebuilding only if necessary..."

docker compose build
docker compose up -d

echo "✅ Smart deploy finished."
