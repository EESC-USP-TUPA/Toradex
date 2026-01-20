ARG BASE_VERSION=3
ARG IMAGE_ARCH=arm64
ARG GPU=vivante
ARG MACHINE=verdin-imx8mm

FROM --platform=linux/${IMAGE_ARCH} torizon/qt5-wayland-imx8:4

RUN apt-get update && apt-get install -y \
    python3 \
    rsync \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY main.py .

CMD ["python3", "main.py"]
