FROM python:3.11-slim

# pip is already installed in this base image

# Install Foxglove Python SDK with pip
RUN pip install foxglove-sdk

WORKDIR /app
COPY telemetry.py /app/telemetry.py

CMD ["python", "telemetry.py"]
