import socket
import json
import logging
import threading
import time
from kalman_speed import SpeedKalman

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000

OUTPUT_PORT = 7001


# ==========================================================
# CLASSE DE DERIVADA MULTI-EIXO
# ==========================================================
class RealTimeDerivative:
    def __init__(self):
        self.last_value = {}
        self.last_time = {}

    def calculate(self, name, current_value):
        current_time = time.time()
        
        if name not in self.last_value or name not in self.last_time:
            self.last_value[name] = current_value
            self.last_time[name] = current_time
            return 0.0

        dt = current_time - self.last_time[name]

        if dt <= 0.0001:
            return 0.0

        derivative = (current_value - self.last_value[name]) / dt

        self.last_value[name] = current_value
        self.last_time[name] = current_time

        return derivative


class ControlECU:
    def __init__(self):
        self.kalman = SpeedKalman()
        # Inicializa a derivada do ângulo
        self.angle_derivative = RealTimeDerivative()
        self.clients = []

    def start(self):
        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.output_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.output_socket.bind(("0.0.0.0", OUTPUT_PORT))
        self.output_socket.listen(5)

        logging.info(f"🟢 Control output listening on {OUTPUT_PORT}")

        threading.Thread(target=self.accept_clients, daemon=True).start()
        threading.Thread(target=self.connect_to_acquisition, daemon=True).start()

        while True:
            time.sleep(1)

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
                        raise ConnectionError("Connection closed")

                    buffer += data.decode()

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue

                        msg = json.loads(line)
                        self.process_message(msg)

            except Exception as e:
                logging.error(f"Acquisition connection error: {e}")
                time.sleep(2)

    def accept_clients(self):
        while True:
            client, addr = self.output_socket.accept()
            client.settimeout(0.05) # Gambiarra de segurança para não travar
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
        data_list = []
        
        # Extração flexível de nome e valor
        name = msg.get("n")
        value = msg.get("v")
        
        imu_accel = None
        gps_speed = None
        angle_position = None

        # 1. Verifica Aceleração (formato antigo com source ou novo plano)
        if name in ["/IMU/lin_accel_x", "IMU/lin_accel_x"]:
            imu_accel = value
        elif msg.get("source") == "imu":
            for signal in msg.get("signals", []):
                if signal.get("name") in ["/IMU/lin_accel_x", "IMU/lin_accel_x"]:
                    imu_accel = signal.get("value")

        # 2. Verifica Velocidade GPS
        if name in ["/GPS/speed", "GPS/speed", "gps_speed"]:
            gps_speed = value
        elif msg.get("source") == "gps":
            gps_speed = msg.get("speed")

        # 3. Verifica Ângulos
        if name in ["/IMU/yaw", "IMU/yaw", "/IMU/roll", "IMU/roll", "/IMU/pitch", "IMU/pitch"]:
            angle_position = value

        # ======================================================
        # CÁLCULOS
        # ======================================================
        if angle_position is not None:
            angle_velocity = self.angle_derivative.calculate(name, angle_position)
            data_list.append({"n": f"{name}_derivative", "v": float(angle_velocity)})

        imu_predicted = None
        kalman_speed = None

        if imu_accel is not None:
            imu_predicted = self.kalman.predict(imu_accel)

        if gps_speed is not None:
            kalman_speed = self.kalman.update(gps_speed)
        else:
            kalman_speed = imu_predicted

        if kalman_speed is not None:
            # Garante float nativo
            try:
                k_val = float(kalman_speed)
            except:
                k_val = float(kalman_speed[0])
            data_list.append({"n": "kalman_speed_filtered", "v": k_val})

        # ======================================================
        # BROADCAST COM LOG DE DEBUG
        # ======================================================
        for data in data_list:
            payload = {"v": data.get("v"), "n": data.get("n")}
            logging.info(f"🚀 Enviando: {payload}")
            self.broadcast(payload)


if __name__ == "__main__":
    ecu = ControlECU()
    ecu.start()