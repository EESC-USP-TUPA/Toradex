import socket
import json
import time
import logging
from foxglove_sender import FoxgloveSender

logging.basicConfig(level=logging.INFO)

# Acquisition runs in host mode
ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000

RECONNECT_DELAY = 2


def connect_to_acquisition():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((ACQUISITION_HOST, ACQUISITION_PORT))
    return sock


def main():

    # Start Foxglove WebSocket server
    fox = FoxgloveSender(port=9000)
    fox.start()

    while True:

        try:
            logging.info("Connecting to acquisition...")
            sock = connect_to_acquisition()
            logging.info("Connected to acquisition")

            buffer = ""

            while True:
                data = sock.recv(4096)
                if not data:
                    raise ConnectionError("Connection closed")

                buffer += data.decode()

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    if not line.strip():
                        continue

                    try:
                        msg = json.loads(line)

                        # =====================================================
                        # CAN DATA
                        # =====================================================
                        if msg.get("source") == "can":

                            timestamp = msg.get("timestamp_ns", time.time_ns())
                            signals = msg.get("signals", {})

                            for name, value in signals.items():

                                if isinstance(value, (int, float)):

                                    fox.send_message(
                                        f"/CAN/{name}",
                                        {
                                            "value": value,
                                            "unit": "",
                                            "timestamp_ns": timestamp
                                        }
                                    )

                        # =====================================================
                        # IMU DATA (BNO055 STRUCTURE)
                        # =====================================================
                        elif msg.get("source") == "imu":

                            timestamp = msg.get("timestamp_ns", time.time_ns())
                            signals = msg.get("signals", [])

                            for signal in signals:

                                name = signal.get("name")
                                value = signal.get("value")
                                unit = signal.get("unit", "")

                                if name and isinstance(value, (int, float)):

                                    fox.send_message(
                                        name,
                                        {
                                            "value": value,
                                            "unit": unit,
                                            "timestamp_ns": timestamp
                                        }
                                    )

                    except Exception as e:
                        logging.error(f"Invalid JSON line: {e}")

        except Exception as e:
            logging.error(f"Acquisition connection error: {e}")
            logging.info(f"Reconnecting in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)


if __name__ == "__main__":
    main()
