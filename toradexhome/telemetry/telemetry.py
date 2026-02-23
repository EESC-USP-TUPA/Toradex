import socket
import json
import time
import logging
import threading
from foxglove_sender import FoxgloveSender

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000

CONTROL_HOST = "127.0.0.1"
CONTROL_PORT = 7001

RECONNECT_DELAY = 2


# ==========================================================
# CONNECTION HELPERS
# ==========================================================

def connect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((host, port))
    return sock


# ==========================================================
# ACQUISITION LISTENER (UNCHANGED LOGIC)
# ==========================================================

def acquisition_listener(fox):

    while True:
        try:
            logging.info("Connecting to acquisition...")
            sock = connect(ACQUISITION_HOST, ACQUISITION_PORT)
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

                        # CAN
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

                        # IMU
                        elif msg.get("source") == "imu":

                            for signal in msg.get("signals", []):
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

                        # GPS
                        elif msg.get("source") == "gps":

                            if "latitude" in msg and "longitude" in msg:

                                fox.send_message(
                                    "/GPS",
                                    {
                                        "latitude": msg["latitude"],
                                        "longitude": msg["longitude"],
                                        "altitude": msg.get("altitude", 0.0),
                                        "speed": msg.get("speed", 0.0),
                                        "heading": msg.get("heading", 0.0),
                                        "satellites": msg.get("satellites", 0),
                                        "fix": msg.get("fix", 0),
                                        "timestamp_ns": timestamp
                                    }
                                )

                    except Exception as e:
                        logging.error(f"Invalid JSON line: {e}")

        except Exception as e:
            logging.error(f"Acquisition connection error: {e}")
            logging.info(f"Reconnecting acquisition in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)


# ==========================================================
# CONTROL LISTENER (NEW)
# ==========================================================

def control_listener(fox):

    while True:
        try:
            logging.info("Connecting to control...")
            sock = connect(CONTROL_HOST, CONTROL_PORT)
            logging.info("Connected to control")

            buffer = ""

            while True:

                data = sock.recv(4096)
                if not data:
                    raise ConnectionError("Control connection closed")

                buffer += data.decode()

                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)

                    if not line.strip():
                        continue

                    msg = json.loads(line)
                    timestamp = time.time_ns()

                    # GPS RAW SPEED
                    if msg.get("gps_speed_raw") is not None:
                        fox.send_message(
                            "/control/speed/gps_raw",
                            {
                                "value": msg["gps_speed_raw"],
                                "unit": "m/s",
                                "timestamp_ns": timestamp
                            }
                        )

                    # IMU PREDICTED SPEED
                    if msg.get("imu_speed_predicted") is not None:
                        fox.send_message(
                            "/control/speed/imu_predicted",
                            {
                                "value": msg["imu_speed_predicted"],
                                "unit": "m/s",
                                "timestamp_ns": timestamp
                            }
                        )

                    # KALMAN FILTERED SPEED
                    if msg.get("kalman_speed_filtered") is not None:
                        fox.send_message(
                            "/control/speed/kalman_filtered",
                            {
                                "value": msg["kalman_speed_filtered"],
                                "unit": "m/s",
                                "timestamp_ns": timestamp
                            }
                        )

                    # COVARIANCE
                    if msg.get("kalman_covariance") is not None:
                        fox.send_message(
                            "/control/speed/kalman_covariance",
                            {
                                "value": msg["kalman_covariance"],
                                "unit": "",
                                "timestamp_ns": timestamp
                            }
                        )

        except Exception as e:
            logging.error(f"Control connection error: {e}")
            logging.info(f"Reconnecting control in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)


# ==========================================================
# MAIN
# ==========================================================

def main():

    fox = FoxgloveSender(port=9000)
    fox.start()

    # Run both listeners in parallel
    threading.Thread(target=acquisition_listener, args=(fox,), daemon=True).start()
    threading.Thread(target=control_listener, args=(fox,), daemon=True).start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
