#!/bin/bash
# ============================
# CONFIG
# ============================
GITHUB_USER="controletupa"
REPO="EESC-USP-TUPA/Toradex"
HOME_DIR="/home/torizon"
TOKEN_FILE="$HOME_DIR/.github_token"

if [ ! -f "$TOKEN_FILE" ]; then
    echo "❌ Arquivo de token não encontrado: $TOKEN_FILE"
    exit 1
fi

GITHUB_TOKEN=$(cat "$TOKEN_FILE" | tr -d '[:space:]')
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ O arquivo de token está vazio!"
    exit 1
fi

echo "🚀 Iniciando atualização via GitHub..."

# ============================
# TEMP DIR + CLEANUP
# ============================
TMP_DIR=$(mktemp -d "$HOME_DIR/.tmp_gitrepo.XXXXXX")

cleanup() {
    if [ -n "$TMP_DIR" ] && [ -d "$TMP_DIR" ]; then
        rm -rf "$TMP_DIR"
    fi
}
# Garante que a pasta temporária seja apagada mesmo se o script der erro no meio
trap cleanup EXIT INT TERM HUP

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

        echo "📥 Clonando repositório..."
        git clone --depth 1 "https://${GITHUB_USER}:${GITHUB_TOKEN}@github.com/${REPO}.git" .

        # Proteção: Verifica se a pasta existe no repo para não copiar lixo
        if [ ! -d "toradexhome" ]; then
            echo "❌ Erro: Diretório toradexhome não encontrado no repositório. Abortando."
            exit 1
        fi

        echo "🔄 Atualizando arquivos locais..."
        cd toradexhome

        # Workaround seguro: Só desvincula (rm -f) os arquivos que EXISTEM no GitHub.
        # Isso evita crash de "Text file busy", mas NÃO APAGA seus arquivos locais da Toradex.
        find . -type f | while IFS= read -r file; do
            rm -f "/workspace/${file#./}" 2>/dev/null || true
        done

        # Copia todos os arquivos do repo para a Toradex, mantendo as permissões (cp -a)
        cp -a . /workspace/
    '; then
    echo "❌ Erro durante o Git pull ou cópia de arquivos. Atualização abortada."
    exit 1
fi

echo "✅ Arquivos copiados com sucesso."

# ============================
# DOCKER COMPOSE UP
# ============================
if [ -f "$HOME_DIR/docker-compose.yml" ]; then
    docker compose -f "$HOME_DIR/docker-compose.yml" up -d --remove-orphans
    echo "🐳 Containers Docker atualizados."
else
    echo "⚠️ Arquivo docker-compose.yml não encontrado em $HOME_DIR. Pulando reinicialização dos containers."
fi

echo "🎉 Deploy finalizado com segurança."