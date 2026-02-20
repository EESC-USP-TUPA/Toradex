#!/bin/bash

USB_MOUNT_POINT="/var/rootdirs/media/EE8D-F793"
COMPOSE_PROJECT_DIR="/home/torizon"
MAIN_CONTAINER="torizon-testetoradex-1"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

restart_main_container() {
    log "🔄 Reiniciando container principal: $MAIN_CONTAINER"
    cd $COMPOSE_PROJECT_DIR

    if docker restart $MAIN_CONTAINER 2>/dev/null; then
        log "✅ Container $MAIN_CONTAINER reiniciado com sucesso"
        sleep 3
        return 0
    else
        log "⚠️  Falha ao reiniciar container $MAIN_CONTAINER"
        return 1
    fi
}

start_usb_transfer() {
    log "✅ Pendrive conectado - Tentando iniciar container usb-transfer"
    cd $COMPOSE_PROJECT_DIR

    if docker-compose up -d usb-transfer 2>/dev/null; then
        log "✅ Container usb-transfer iniciado com sucesso"
        return 0
    else
        log "⚠️  Falha ao iniciar container (bind mount pode não estar pronto)"
        return 1
    fi
}

stop_usb_transfer() {
    log "❌ Pendrive desconectado - Parando container usb-transfer"
    cd $COMPOSE_PROJECT_DIR

    docker-compose stop usb-transfer 2>/dev/null
    docker-compose rm -f usb-transfer 2>/dev/null

    log "🗑️  Container usb-transfer parado e removido"
}

is_usb_connected() {
    [ -d "$USB_MOUNT_POINT" ] && [ "$(ls -A "$USB_MOUNT_POINT" 2>/dev/null)" ]
}

is_container_running() {
    docker ps --filter "name=$1" --format "{{.Names}}" | grep -q "^$1$"
}

main() {
    log "🔌 Iniciando monitoramento USB..."

    last_state="disconnected"
    retry_count=0
    max_retries=5
    container_started=false

    while true; do
        if is_usb_connected; then
            if [ "$last_state" != "connected" ]; then
                log "📌 USB detectado - Iniciando processo de transferência"
                last_state="connected"
                retry_count=0
                container_started=false
            fi

            # Tenta iniciar o container usb-transfer (com retry se falhar)
            if ! is_container_running "usb-transfer"; then
                if [ "$container_started" = true ]; then
                    log "⚠️  Container usb-transfer parou inesperadamente"
                else
                    if start_usb_transfer; then
                        retry_count=0
                        container_started=true
                    else
                        retry_count=$((retry_count + 1))
                        if [ $retry_count -lt $max_retries ]; then
                            log "🔄 Tentativa $retry_count/$max_retries em 5 segundos..."
                            sleep 5
                        else
                            log "💤 Muitas falhas - Aguardando 30 segundos antes de tentar novamente"
                            sleep 30
                            retry_count=0
                        fi
                    fi
                fi
            fi

        else
            if [ "$last_state" != "disconnected" ]; then
                stop_usb_transfer
                restart_main_container  # Agora reinicia o container principal após a transferência
                last_state="disconnected"
                retry_count=0
                container_started=false
                log "⏳ Aguardando nova conexão do pendrive..."
            fi
        fi

        sleep 5
    done
}

main

