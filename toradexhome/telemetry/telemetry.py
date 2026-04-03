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
# ACQUISITION LISTENER (OPTIMIZED)
# ==========================================================

def acquisition_listener(fox):
    last_sent_times = {}
    MIN_INTERVAL_NS = 50_000_000  # 50ms = 20Hz update limit

    while True:
        try:
            logging.info("Connecting to acquisition...")
            sock = connect(ACQUISITION_HOST, ACQUISITION_PORT)
            logging.info("Connected to acquisition")

            # Use makefile for high-speed line reading
            sock_file = sock.makefile('r', encoding='utf-8')

            while True:
                line = sock_file.readline()
                
                if not line:
                    raise ConnectionError("Acquisition connection closed")

                if not line.strip():
                    continue

                try:
                    msg = json.loads(line)
                    timestamp = msg.get("timestamp_ns", time.time_ns())

                    if msg.get("source") == "can":
                        signals = msg.get("signals", {})
                        for name, value in signals.items():
                            if isinstance(value, (int, float)):
                                topic = f"/CAN/{name}"
                                last_time = last_sent_times.get(topic, 0)
                                if (timestamp - last_time) >= MIN_INTERVAL_NS:
                                    fox.send_message(topic, {"value": value, "unit": "", "timestamp_ns": timestamp})
                                    last_sent_times[topic] = timestamp

                    elif msg.get("source") == "imu":
                        for signal in msg.get("signals", []):
                            name = signal.get("name")
                            value = signal.get("value")
                            if name and isinstance(value, (int, float)):
                                last_time = last_sent_times.get(name, 0)
                                if (timestamp - last_time) >= MIN_INTERVAL_NS:
                                    fox.send_message(name, {"value": value})
                                    last_sent_times[name] = timestamp

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
                    logging.error(f"Invalid JSON line in acquisition: {e}")

        except Exception as e:
            logging.error(f"Acquisition connection error: {e}")
            logging.info(f"Reconnecting acquisition in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)

# ==========================================================
# CONTROL LISTENER (OPTIMIZED)
# ==========================================================

def control_listener(fox):
    while True:
        try:
            logging.info("Connecting to control...")
            sock = connect(CONTROL_HOST, CONTROL_PORT)
            logging.info("Connected to control")

            # Use makefile for high-speed line reading
            sock_file = sock.makefile('r', encoding='utf-8')

            while True:
                line = sock_file.readline()
                
                if not line:
                    raise ConnectionError("Control connection closed")

                if not line.strip():
                    continue

                try:
                    msg = json.loads(line)
                    timestamp = time.time_ns()

                    if msg.get("gps_speed_raw") is not None:
                        fox.send_message("/control/speed/gps_raw", {"value": msg["gps_speed_raw"], "unit": "m/s", "timestamp_ns": timestamp})

                    if msg.get("imu_speed_predicted") is not None:
                        fox.send_message("/control/speed/imu_predicted", {"value": msg["imu_speed_predicted"], "unit": "m/s", "timestamp_ns": timestamp})

                    if msg.get("kalman_speed_filtered") is not None:
                        fox.send_message("/control/speed/kalman_filtered", {"value": msg["kalman_speed_filtered"], "unit": "m/s", "timestamp_ns": timestamp})

                    if msg.get("kalman_covariance") is not None:
                        fox.send_message("/control/speed/kalman_covariance", {"value": msg["kalman_covariance"], "unit": "", "timestamp_ns": timestamp})

                except Exception as e:
                    logging.error(f"Invalid JSON line in control: {e}")

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

    threading.Thread(target=acquisition_listener, args=(fox,), daemon=True).start()
    threading.Thread(target=control_listener, args=(fox,), daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
