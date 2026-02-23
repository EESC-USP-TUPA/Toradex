import socket
import json
import logging
from kalman_speed import SpeedKalman

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000
OUTPUT_PORT = 7001


class ControlECU:
    def __init__(self):
        self.kalman = SpeedKalman()
        self.clients = []

    def start(self):

        # Output server (Telemetry connects here)
        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.output_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.output_socket.bind(("0.0.0.0", OUTPUT_PORT))
        self.output_socket.listen(5)

        logging.info(f"🟢 Control output listening on {OUTPUT_PORT}")

        import threading
        threading.Thread(target=self.accept_clients, daemon=True).start()

        # Connect to Acquisition (do NOT bind 7000)
        self.connect_to_acquisition()

    def connect_to_acquisition(self):
        while True:
            try:
                logging.info("🔄 Connecting to acquisition...")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((ACQUISITION_HOST, ACQUISITION_PORT))
                logging.info("✅ Connected to acquisition")

                buffer = ""

                while True:
                    data = sock.recv(4096)
                    if not data:
                        break

                    buffer += data.decode()

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)

                        if not line.strip():
                            continue

                        msg = json.loads(line)
                        self.process_message(msg)

            except Exception as e:
                logging.error(f"Acquisition connection error: {e}")

    def accept_clients(self):
        while True:
            client, addr = self.output_socket.accept()
            logging.info(f"🔗 Telemetry connected: {addr}")
            self.clients.append(client)

    def broadcast(self, message):
        dead = []
        data = (json.dumps(message) + "\n").encode()

        for client in self.clients:
            try:
                client.sendall(data)
            except:
                dead.append(client)

        for d in dead:
            self.clients.remove(d)

    def process_message(self, msg):

        imu_accel = msg.get("imu_accel")
        gps_speed = msg.get("gps_speed")

        imu_predicted = None
        kalman_speed = None

        if imu_accel is not None:
            imu_predicted = self.kalman.predict(imu_accel)

        if gps_speed is not None:
            kalman_speed = self.kalman.update(gps_speed)
        else:
            kalman_speed = imu_predicted

        if kalman_speed is None:
            return

        output = {
            "gps_speed_raw": gps_speed,
            "imu_speed_predicted": imu_predicted,
            "kalman_speed_filtered": kalman_speed,
            "kalman_covariance": self.kalman.P
        }

        self.broadcast(output)


if __name__ == "__main__":
    ecu = ControlECU()
    ecu.start()
