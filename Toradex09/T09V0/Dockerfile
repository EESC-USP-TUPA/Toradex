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
    torizon/wayland-base-vivante:3 AS Base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-can \
    can-utils \
    iproute2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src ./src

# Configure CAN interface and run
CMD ["sh", "-c", "ip link set can0 down || true && \
     ip link set can0 type can bitrate 250000 && \
     ip link set can0 up && \
     python3 src/main.py"]
