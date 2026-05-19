#!/bin/bash

# ============================
# CONFIG
# ============================

GITHUB_USER="controletupa"
REPO="EESC-USP-TUPA/Toradex"
HOME_DIR="/home/torizon"
TOKEN_FILE="$HOME_DIR/.github_token"

if [ ! -f "$TOKEN_FILE" ]; then
  echo "❌ Token file not found: $TOKEN_FILE"
  exit 1
fi

GITHUB_TOKEN=$(cat "$TOKEN_FILE" | tr -d '[:space:]')

if [ -z "$GITHUB_TOKEN" ]; then
  echo "❌ Token file is empty!"
  exit 1
fi

echo "🚀 Pull starting..."

# Safe cleanup function for traps
TMP_DIR=""
cleanup() {
  if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT INT TERM HUP

# Create temporary directory on persistent storage, not RAM
TMP_DIR=$(mktemp -d "$HOME_DIR/.tmp_gitrepo.XXXXXX")

# Execute rootless docker pull and safe file replacement
if ! docker run --rm \
  --user $(id -u):$(id -g) \
  -e GITHUB_TOKEN="$GITHUB_TOKEN" \
  -e GITHUB_USER="$GITHUB_USER" \
  -e REPO="$REPO" \
  -v "$HOME_DIR:/workspace" \
  -v "$TMP_DIR:/gitrepo" \
  --entrypoint /bin/sh \
  alpine/git \
  -c '
    cd /gitrepo && \
    echo "📥 Cloning repository..." && \
    git clone --depth 1 "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${REPO}.git" . && \
    
    # STRICT DIRECTORY ENFORCEMENT
    if [ ! -d "toradexhome" ]; then \
      echo "❌ Error: toradexhome directory not found in repository. Aborting to prevent root pollution."; \
      exit 1; \
    fi && \
    
    echo "🔄 Updating local files..." && \
    cd toradexhome && \
    
    # Safely unlink destination files before copying to prevent in-place execution crashes
    find . -type f | while read -r file; do \
      rm -f "/workspace/$file" 2>/dev/null; \
    done && \
    
    # Perform the actual copy
    cp -rf . /workspace/
  '; then
  echo "❌ Error during Git pull or file update. Aborting deployment."
  exit 1
fi

echo "✅ Git pull and file update done."

# Only attempt to spin up Docker if the compose file actually exists 
if [ -f "$HOME_DIR/docker-compose.yml" ]; then
  docker compose -f "$HOME_DIR/docker-compose.yml" up -d --remove-orphans
  echo "🐳 Docker stack updated."
else
  echo "⚠️ No docker-compose.yml found in $HOME_DIR. Skipping container deployment."
fi

echo "🎉 Pull and deploy finished."
