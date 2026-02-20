FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y i2c-tools && \
    pip install smbus2 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY bno055.py .

CMD ["python3", "bno055.py"]
