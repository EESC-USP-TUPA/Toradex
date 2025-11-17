ARG BASE_VERSION=3

##
# Board architecture
# arm or arm64
##
ARG IMAGE_ARCH=arm64

##
# Board GPU vendor prefix
##
ARG GPU=vivante

##
# SoM
##
ARG MACHINE=verdin-imx8mm

# BUILD ------------------------------------------------------------------------
FROM --platform=linux/${IMAGE_ARCH} \
     torizon/qt5-wayland-imx8:4 AS deploy

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-can \
    can-utils \
    iproute2 \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Configuração do timezone para horário de Brasília
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Criar e ativar ambiente virtual
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Copiar requirements primeiro para cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY src ./src

# Configurar interface CAN e executar a aplicação
CMD ["sh", "-c", "ip link set can0 down || true && \
     ip link set can0 type can bitrate 250000 && \
     ip link set can0 up && \
     python3 src/main.py"]
