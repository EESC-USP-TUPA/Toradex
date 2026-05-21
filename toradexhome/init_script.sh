#!/bin/bash

# Conectar ao Wi-Fi
nmcli dev wifi connect 'lulusenta' password 'poscrias'

# Atualizar arquivos do GitHub (falha não impede inicialização)
if /home/torizon/pull.sh; then
    echo "✅ Pull concluído com sucesso."
else
    echo "⚠️  Pull falhou (sem Wi-Fi?). Iniciando com arquivos locais."
fi

# Configurar a interface CAN
ip link set can0 down
sleep 1
ip link set can0 type can bitrate 250000
sleep 1
ip link set can0 up
sleep 1

# Rodar Docker Compose
cd /home/torizon/
docker-compose up -d --remove-orphans testetoradex weston acquisition control telemetry

/home/torizon/usb-monitor.sh