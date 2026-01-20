ARG IMAGE_ARCH=arm64v8
FROM torizon/${IMAGE_ARCH}-debian-base@sha256:e52e2f7288f4476b3b415fb644265fd5627823086977cfdf563b5a31911854be

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
COPY can_receiver.py .

# Configure CAN interface and run
CMD ["sh", "-c", "ip link set can0 up type can bitrate 500000 && python3 can_receiver.py"]