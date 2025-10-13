# ARGUMENTS --------------------------------------------------------------------
##
# Board architecture
##
ARG IMAGE_ARCH=arm64

##
# Base container version
##
ARG BASE_VERSION=3.3.0-bookworm

##
# Directory of the application inside container
##
ARG APP_ROOT=/app

FROM --platform=linux/${IMAGE_ARCH} \
    torizon/debian:${BASE_VERSION} AS Deploy

ARG IMAGE_ARCH
ARG APP_ROOT

# Install required packages
RUN apt-get -q -y update && \
    apt-get -q -y install \
    python3-minimal \
    python3-pip \
    python3-venv \
    libopenjp2-7 \
    libtiff6 \
    build-essential \
    python3-dev \
    # Pillow dependencies
    # DO NOT REMOVE THIS LABEL: this is used for VS Code automation
    # __torizon_packages_prod_start__
    # __torizon_packages_prod_end__
    # DO NOT REMOVE THIS LABEL: this is used for VS Code automation
    && apt-get clean && apt-get autoremove && \
    rm -rf /var/lib/apt/lists/*

# Create virtualenv
RUN python3 -m venv ${APP_ROOT}/.venv --system-site-packages

# Install pip packages on venv
COPY requirements-release.txt /requirements-release.txt
RUN . ${APP_ROOT}/.venv/bin/activate && \
    pip3 install --upgrade pip && \
    pip3 install -r requirements-release.txt && \
    rm requirements-release.txt && \
    # Remove build tools to reduce image size
    apt-get purge -y build-essential python3-dev && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*
# Copy the application source code

COPY ./src ${APP_ROOT}/src

WORKDIR ${APP_ROOT}

ENV APP_ROOT=${APP_ROOT}
# Activate and run the code
CMD ["sh", "-c", ". ${APP_ROOT}/.venv/bin/activate && python3 src/main.py"]