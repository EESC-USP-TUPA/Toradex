import os
import json
import socket
import threading
import time
import logging

from can_receiver import CANReceiver
from can_sender import CANSender
from can_decoder import CANDecoderCore
from bno055 import start as start_imu


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

CAN_INTERFACE = os.getenv("CAN_INTERFACE", "can0")
RX_PORT = int(os.getenv("RX_STREAM_PORT", "7000"))
TX_PORT = int(os.getenv("TX_COMMAND_PORT", "7001"))

clients = []
clients_lock = threading.Lock()

decoder = CANDecoderCore()
sender = CANSender(interface=CAN_INTERFACE)


# =========================================================
# BROADCAST (Low-latency + Safe)
# =========================================================

def broadcast(payload):

    try:
        raw = (json.dumps(payload, separators=(",", ":")) + "\n").encode()
    except Exception as e:
        logging.error(f"JSON encode error: {e}")
        return

    dead_clients = []

    with clients_lock:
        for c in clients:
            try:
                c.sendall(raw)
            except Exception:
                dead_clients.append(c)

        for d in dead_clients:
            try:
                d.close()
            except:
                pass
            clients.remove(d)


# =========================================================
# CAN CALLBACK
# =========================================================

def handle_can(msg):

    decoded = decoder.decode(msg)

    if not decoded:
        return

    payload = {
        "source": "can",
        "timestamp_ns": time.time_ns(),
        "can_id": hex(msg.arbitration_id),
        "signals": decoded
    }

    broadcast(payload)


# =========================================================
# RX SERVER (Telemetry stream out)
# =========================================================

def start_rx_server():

    def server():

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind(("0.0.0.0", RX_PORT))
        sock.listen(10)

        logging.info(f"JSON stream available on port {RX_PORT}")

        while True:
            conn, addr = sock.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            logging.info(f"Telemetry client connected: {addr}")

            with clients_lock:
                clients.append(conn)

    threading.Thread(target=server, daemon=True).start()


# =========================================================
# TX SERVER (CAN command input)
# =========================================================

def start_tx_server():

    def server():

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind(("0.0.0.0", TX_PORT))
        sock.listen(5)

        logging.info(f"CAN command server on port {TX_PORT}")

        while True:
            conn, addr = sock.accept()
            logging.info(f"TX client connected: {addr}")

            threading.Thread(
                target=handle_tx_client,
                args=(conn,),
                daemon=True
            ).start()

    threading.Thread(target=server, daemon=True).start()


def handle_tx_client(conn):

    buffer = ""

    with conn:
        while True:

            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode()

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                try:
                    msg = json.loads(line)

                    can_id = int(msg["can_id"], 16)
                    payload = msg["data"]
                    extended = msg.get("extended", False)

                    sender.send(can_id, payload, extended)

                except Exception as e:
                    logging.error(f"Invalid CAN TX request: {e}")


# =========================================================
# MAIN
# =========================================================

def main():

    logging.info("Starting Acquisition Gateway")

    sender.connect()

    start_rx_server()
    start_tx_server()

    # 200 Hz IMU (Torque Vectoring Ready)
    start_imu(callback=broadcast, rate_hz=200)

    # CAN receiver (blocking loop)
    receiver = CANReceiver(interface=CAN_INTERFACE)
    receiver.start_receiving(handle_can)


if __name__ == "__main__":
    main()
