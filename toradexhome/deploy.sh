#!/bin/bash

# ============================
# CONFIG
# ============================

GITHUB_USER="controletupa"
REPO="EESC-USP-TUPA/Toradex"
HOME_DIR="/home/torizon"

TOKEN_FILE="$HOME/.github_token"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "❌ Token file not found: $TOKEN_FILE"
  exit 1
fi

GITHUB_TOKEN=$(cat $TOKEN_FILE)
REPO_URL="https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${REPO}.git"

echo "🚀 Deploy starting..."

TMP_DIR=$(mktemp -d)

docker run --rm \
  -v $HOME_DIR:/workspace \
  -v $TMP_DIR:/gitrepo \
  --entrypoint /bin/sh \
  alpine/git \
  -c "
    git config --global user.email 'tupa@toradex.local' && \
    git config --global user.name 'Toradex Auto Deploy' && \
    git config --global --add safe.directory /gitrepo && \
    cd /gitrepo && \
    git clone $REPO_URL . && \
    DEFAULT_BRANCH=\$(git symbolic-ref --short refs/remotes/origin/HEAD | sed 's@^origin/@@') && \
    mkdir -p toradexhome && \
    cp -r /workspace/* toradexhome/ && \
    rm -rf toradexhome/Toradex 2>/dev/null || true && \
    git add . && \
    git commit -m 'Auto deploy: \$(date)' || true && \
    git push origin \$DEFAULT_BRANCH
  "

echo "✅ Git push done."

docker compose -f $HOME_DIR/docker-compose.yml up -d

echo "🐳 Docker restarted."
echo "🎉 Deploy finished."
