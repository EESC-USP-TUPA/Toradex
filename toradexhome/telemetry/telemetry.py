import socket
import json
import time
import logging
from foxglove_sender import FoxgloveSender

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000


def main():

    fox = FoxgloveSender(port=9000)
    fox.start()

    while True:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ACQUISITION_HOST, ACQUISITION_PORT))
            logging.info("Connected to acquisition")

            while True:
                data = sock.recv(4096)
                if not data:
                    break

                lines = data.decode().splitlines()

                for line in lines:
                    try:
                        msg = json.loads(line)

                        # CAN signals
                        if msg.get("source") == "can":
                            signals = msg.get("signals", {})
                            for name, value in signals.items():
                                fox.send_message(
                                    f"/CAN/{name}",
                                    {
                                        "value": value,
                                        "unit": "",
                                        "timestamp_ns": msg["timestamp_ns"]
                                    }
                                )

                        # IMU data (if start_imu uses broadcast)
                        else:
                            for key, value in msg.items():
                                if isinstance(value, (int, float)):
                                    fox.send_message(
                                        f"/IMU/{key}",
                                        {
                                            "value": value,
                                            "unit": "",
                                            "timestamp_ns": time.time_ns()
                                        }
                                    )

                    except Exception as e:
                        logging.error(f"Invalid JSON: {e}")

        except Exception as e:
            logging.error("Connection lost. Retrying...")
            time.sleep(2)


if __name__ == "__main__":
    main()
