import socket
import json
import time
import logging
import os
from datetime import datetime
from collections import defaultdict, deque

from foxglove_sender import FoxgloveSender
from mcap.writer import Writer

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000
RECONNECT_DELAY = 2

MCAP_FOLDER = "/logs"
os.makedirs(MCAP_FOLDER, exist_ok=True)

# 200 Hz input → 20 Hz output
MOVING_WINDOW = 10
PUBLISH_DIVIDER = 10


# =========================================================
# MCAP RECORDER (FULL RAW DATA @200Hz)
# =========================================================

class MCAPRecorder:

    def __init__(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.file_path = os.path.join(MCAP_FOLDER, f"telemetry_{timestamp}.mcap")
        self.file = open(self.file_path, "wb")
        self.writer = Writer(self.file)
        self.writer.start()

        self.schema_id = self.writer.register_schema(
            name="json",
            encoding="jsonschema",
            data=b'{"type":"object"}'
        )

        self.channels = {}

        logging.info(f"Recording MCAP → {self.file_path}")

    def write(self, topic, payload, timestamp_ns):

        if topic not in self.channels:
            channel_id = self.writer.register_channel(
                topic=topic,
                message_encoding="json",
                schema_id=self.schema_id
            )
            self.channels[topic] = channel_id

        self.writer.add_message(
            channel_id=self.channels[topic],
            log_time=timestamp_ns,
            publish_time=timestamp_ns,
            data=json.dumps(payload).encode()
        )

    def close(self):
        self.writer.finish()
        self.file.close()


# =========================================================
# MOVING AVERAGE FILTER (20Hz)
# =========================================================

class MovingAverage:

    def __init__(self):
        self.buffers = defaultdict(lambda: deque(maxlen=MOVING_WINDOW))
        self.counter = 0

    def process(self, topic, value):

        self.buffers[topic].append(value)
        self.counter += 1

        # Downsample 200Hz → 20Hz
        if self.counter % PUBLISH_DIVIDER != 0:
            return None

        return sum(self.buffers[topic]) / len(self.buffers[topic])


# =========================================================
# CONNECT TO ACQUISITION
# =========================================================

def connect():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((ACQUISITION_HOST, ACQUISITION_PORT))
    return sock


# =========================================================
# MAIN
# =========================================================

def main():

    fox = FoxgloveSender(port=9000)
    fox.start()

    recorder = MCAPRecorder()
    filter = MovingAverage()

    while True:

        try:
            logging.info("Connecting to acquisition...")
            sock = connect()
            logging.info("Connected.")

            buffer = ""

            while True:

                data = sock.recv(4096)
                if not data:
                    raise ConnectionError("Lost connection")

                buffer += data.decode()

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    if not line.strip():
                        continue

                    msg = json.loads(line)
                    timestamp = msg.get("timestamp_ns", time.time_ns())

                    # =================================================
                    # 1️⃣ SAVE FULL RAW MESSAGE TO MCAP
                    # =================================================
                    recorder.write("/raw", msg, timestamp)

                    # =================================================
                    # 2️⃣ SEND MOVING AVERAGE (VALUES ONLY) TO FOXGLOVE
                    # =================================================

                    if msg.get("source") == "imu":

                        for signal in msg.get("signals", []):
                            name = signal["name"]
                            value = signal["value"]

                            avg = filter.process(name, value)

                            if avg is not None:
                                fox.send_message(
                                    name,
                                    {
                                        "value": avg,
                                        "timestamp_ns": timestamp
                                    }
                                )

                    elif msg.get("source") == "can":

                        for name, value in msg.get("signals", {}).items():

                            topic = f"/CAN/{name}"

                            avg = filter.process(topic, value)

                            if avg is not None:
                                fox.send_message(
                                    topic,
                                    {
                                        "value": avg,
                                        "timestamp_ns": timestamp
                                    }
                                )

        except Exception as e:
            logging.error(f"Connection error: {e}")
            time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()
