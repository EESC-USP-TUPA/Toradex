# -------------------------------------------------
# Base Image
# -------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------
# Environment
# -------------------------------------------------
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# -------------------------------------------------
# Install system dependencies
# -------------------------------------------------
RUN apt-get update && \
    apt-get install -y \
        iproute2 \
        can-utils \
        i2c-tools \
        libgpiod-dev \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Install Python dependencies
# -------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------
# Copy application files
# -------------------------------------------------
COPY main.py .
COPY can_receiver.py .
COPY can_sender.py .
COPY can_decoder.py .
COPY bno055.py .
COPY neo_m8n.py .

# -------------------------------------------------
# Run acquisition
# -------------------------------------------------
CMD ["python", "main.py"]
