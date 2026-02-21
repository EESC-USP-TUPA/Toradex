import socket
import json
import time
import logging
from foxglove_sender import FoxgloveSender

logging.basicConfig(level=logging.INFO)

class JSONTelemetryReceiver:
    def __init__(self, foxglove_sender, host="0.0.0.0", port=7001):
        self.host = host
        self.port = port
        self.foxglove = foxglove_sender

    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen(1)

        print(f"Listening JSON on port {self.port}")

        while True:
            conn, addr = sock.accept()
            print(f"Connected from {addr}")

            with conn:
                while True:
                    data = conn.recv(4096)
                    if not data:
                        break

                    lines = data.decode().splitlines()

                    for line in lines:
                        try:
                            msg = json.loads(line)

                            topic = msg.get("topic", "/unknown")
                            value = msg.get("value", 0)
                            unit = msg.get("unit", "")

                            payload = {
                                "value": value,
                                "unit": unit,
                                "timestamp_ns": time.time_ns()
                            }

                            self.foxglove.send_message(topic, payload)

                        except Exception as e:
                            print("Invalid JSON:", e)


def main():
    fox_sender = FoxgloveSender(port=9000)
    fox_sender.start()

    receiver = JSONTelemetryReceiver(fox_sender, port=7001)
    receiver.start()


if __name__ == "__main__":
    main()
