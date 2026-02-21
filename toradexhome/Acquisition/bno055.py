import socket
import json
import time
import logging
import os
from datetime import datetime
from collections import defaultdict
from foxglove_sender import FoxgloveSender
from mcap.writer import Writer

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000
RECONNECT_DELAY = 2

MCAP_FOLDER = "/logs"
os.makedirs(MCAP_FOLDER, exist_ok=True)

SAMPLE_RATE = 200.0
CUTOFF_HZ = 1.0   # MINIMUM SAFE CUTOFF


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
# LOW PASS FILTER (1Hz Cutoff)
# =========================================================

class LowPassFilter:

    def __init__(self, cutoff_hz=CUTOFF_HZ, sample_rate=SAMPLE_RATE):

        dt = 1.0 / sample_rate
        rc = 1.0 / (2 * 3.1415926535 * cutoff_hz)
        self.alpha = dt / (rc + dt)

        self.state = {}
        self.counter = 0

    def process(self, topic, value):

        if topic not in self.state:
            self.state[topic] = value

        filtered = self.state[topic] + self.alpha * (value - self.state[topic])
        self.state[topic] = filtered

        self.counter += 1

        # Downsample 200Hz → 20Hz
        if self.counter % 10 != 0:
            return None

        return filtered


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
    filter = LowPassFilter()

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

                    # Save RAW 200Hz
                    recorder.write("/raw", msg, timestamp)

                    if msg.get("source") == "imu":

                        for signal in msg.get("signals", []):
                            name = signal["name"]
                            value = signal["value"]

                            filtered = filter.process(name, value)

                            if filtered is not None:
                                fox.send_message(
                                    name,
                                    {
                                        "value": filtered,
                                        "timestamp_ns": timestamp
                                    }
                                )

        except Exception as e:
            logging.error(f"Connection error: {e}")
            time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()
