#!/bin/bash
# ============================
# CONFIG
# ============================
GITHUB_USER="controletupa"
REPO="EESC-USP-TUPA/Toradex"
HOME_DIR="/home/torizon"
TOKEN_FILE="$HOME_DIR/.github_token"
MANIFEST_FILE="$HOME_DIR/.deployed_manifest"

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

# ============================
# TEMP DIR + CLEANUP
# ============================
TMP_DIR=""
cleanup() {
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}
trap cleanup EXIT INT TERM HUP

# Persistent storage, not RAM
TMP_DIR=$(mktemp -d "$HOME_DIR/.tmp_gitrepo.XXXXXX")
NEW_MANIFEST="$TMP_DIR/new_manifest.txt"

# ============================
# CLONE + COPY via Docker
# ============================
if ! docker run --rm \
    --user "$(id -u):$(id -g)" \
    -e GITHUB_TOKEN="$GITHUB_TOKEN" \
    -e GITHUB_USER="$GITHUB_USER" \
    -e REPO="$REPO" \
    -v "$HOME_DIR:/workspace" \
    -v "$TMP_DIR:/gitrepo" \
    --entrypoint /bin/sh \
    alpine/git \
    -c '
        set -e

        cd /gitrepo

        echo "📥 Cloning repository..."
        git clone --depth 1 "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${REPO}.git" .

        # STRICT DIRECTORY ENFORCEMENT
        if [ ! -d "toradexhome" ]; then
            echo "❌ Error: toradexhome directory not found in repository. Aborting to prevent root pollution."
            exit 1
        fi

        echo "📋 Generating file manifest..."
        # Relative paths from toradexhome/ root — used for orphan detection later
        find toradexhome -type f | sed "s|^toradexhome/||" | sort > /gitrepo/new_manifest.txt

        echo "🔄 Updating local files..."
        cd toradexhome

        # Safely unlink destination files before copying to prevent in-place execution crashes
        find . -type f | while IFS= read -r file; do
            rm -f "/workspace/${file#./}" 2>/dev/null
        done

        # Perform the actual copy
        cp -rf . /workspace/
    '; then
    echo "❌ Error during Git pull or file update. Aborting deployment."
    exit 1
fi

echo "✅ Git pull and file update done."

# ============================
# ORPHAN DELETION
# ============================
if [ -f "$NEW_MANIFEST" ]; then

    if [ -f "$MANIFEST_FILE" ]; then
        echo "🗑️  Checking for orphan files..."

        # Files present in the OLD manifest but absent from the NEW one
        # were removed from the repo and should be deleted locally
        comm -23 \
            <(sort "$MANIFEST_FILE") \
            <(sort "$NEW_MANIFEST") | \
        while IFS= read -r orphan; do
            target="$HOME_DIR/$orphan"
            if [ -f "$target" ]; then
                echo "   🗑️  Deleting orphan: $orphan"
                rm -f "$target"
            fi
        done

        # Clean up empty directories left behind (skip hidden dirs like .tmp_*)
        find "$HOME_DIR" -mindepth 1 -type d -empty \
            ! -path "$HOME_DIR/.*" \
            | sort -r \
            | while IFS= read -r empty_dir; do
                rmdir "$empty_dir" 2>/dev/null \
                    && echo "   📁 Removed empty directory: ${empty_dir#"$HOME_DIR"/}"
            done

    else
        echo "ℹ️  No previous manifest found — skipping orphan cleanup (first run)."
    fi

    # Persist new manifest for the next run
    cp "$NEW_MANIFEST" "$MANIFEST_FILE"
    echo "📋 Manifest saved ($(wc -l < "$MANIFEST_FILE") files tracked)."

else
    echo "⚠️  New manifest not generated inside container. Skipping orphan cleanup."
fi

# ============================
# DOCKER COMPOSE UP
# ============================
if [ -f "$HOME_DIR/docker-compose.yml" ]; then
    docker compose -f "$HOME_DIR/docker-compose.yml" up -d --remove-orphans
    echo "🐳 Docker stack updated."
else
    echo "⚠️  No docker-compose.yml found in $HOME_DIR. Skipping container deployment."
fi

echo "🎉 Pull and deploy finished."