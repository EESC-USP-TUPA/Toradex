import socket
import json
import time
import logging
from foxglove_sender import FoxgloveSender

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000
RECONNECT_DELAY = 2


def connect_to_acquisition():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((ACQUISITION_HOST, ACQUISITION_PORT))
    return sock


def main():

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
                        timestamp = msg.get("timestamp_ns", time.time_ns())

                        # =====================================================
                        # CAN DATA
                        # =====================================================
                        if msg.get("source") == "can":

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
                        # IMU DATA
                        # =====================================================
                        elif msg.get("source") == "imu":

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

                        # =====================================================
                        # GPS DATA (DIRECT FORMAT)
                        # =====================================================
                        elif msg.get("source") == "gps" and "latitude" in msg:

                            fox.send_message(
                                "/GPS",
                                {
                                    "latitude": msg.get("latitude"),
                                    "longitude": msg.get("longitude"),
                                    "altitude": msg.get("altitude", 0.0),
                                    "speed": msg.get("speed", 0.0),
                                    "heading": msg.get("heading", 0.0),
                                    "satellites": msg.get("satellites", 0),
                                    "hdop": msg.get("hdop", 0.0),
                                    "fix": msg.get("fix", 0),
                                    "timestamp_ns": timestamp
                                }
                            )

                        # =====================================================
                        # GPS DATA (SIGNALS LIST FORMAT)
                        # =====================================================
                        elif msg.get("source") == "gps":

                            gps_data = {}

                            for signal in msg.get("signals", []):
                                name = signal.get("name")
                                value = signal.get("value")

                                if name:
                                    gps_data[name] = value

                            if "latitude" in gps_data and "longitude" in gps_data:

                                fox.send_message(
                                    "/GPS",
                                    {
                                        "latitude": gps_data.get("latitude"),
                                        "longitude": gps_data.get("longitude"),
                                        "altitude": gps_data.get("altitude", 0.0),
                                        "speed": gps_data.get("speed", 0.0),
                                        "heading": gps_data.get("heading", 0.0),
                                        "satellites": gps_data.get("satellites", 0),
                                        "hdop": gps_data.get("hdop", 0.0),
                                        "fix": gps_data.get("fix", 0),
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
