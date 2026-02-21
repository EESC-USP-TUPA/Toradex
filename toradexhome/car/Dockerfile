FROM python:3.10-slim

# needed for unix sockets + performance
RUN apt-get update && apt-get install -y \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# install foxglove INSIDE container
RUN pip install foxglove

WORKDIR /app

COPY foxglove_bridge.py .

CMD ["python", "foxglove_bridge.py"]
