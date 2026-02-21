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


logging.basicConfig(level=logging.INFO)

CAN_INTERFACE = os.getenv("CAN_INTERFACE", "can0")
RX_PORT = int(os.getenv("RX_STREAM_PORT", "7000"))
TX_PORT = int(os.getenv("TX_COMMAND_PORT", "7001"))

clients = []
clients_lock = threading.Lock()

decoder = CANDecoderCore()
sender = CANSender(interface=CAN_INTERFACE)


# =========================================================
# BROADCAST
# =========================================================

def broadcast(payload):

    raw = (json.dumps(payload) + "\n").encode()
    dead = []

    with clients_lock:
        for c in clients:
            try:
                c.sendall(raw)
            except:
                dead.append(c)

        for d in dead:
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
        "can_id": hex(msg.arbitration_id),
        "timestamp_ns": time.time_ns(),
        "signals": decoded
    }

    broadcast(payload)


# =========================================================
# TCP SERVERS
# =========================================================

def start_rx_server():

    def server():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", RX_PORT))
        sock.listen(10)

        logging.info(f"JSON stream on port {RX_PORT}")

        while True:
            conn, _ = sock.accept()
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            with clients_lock:
                clients.append(conn)

    threading.Thread(target=server, daemon=True).start()


def start_tx_server():

    def server():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", TX_PORT))
        sock.listen(5)

        logging.info(f"CAN TX server on port {TX_PORT}")

        while True:
            conn, _ = sock.accept()
            threading.Thread(
                target=handle_tx_client,
                args=(conn,),
                daemon=True
            ).start()

    threading.Thread(target=server, daemon=True).start()


def handle_tx_client(conn):

    with conn:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            try:
                msg = json.loads(data.decode())
                can_id = int(msg["can_id"], 16)
                payload = msg["data"]
                extended = msg.get("extended", False)

                sender.send(can_id, payload, extended)

            except Exception as e:
                logging.error(f"Invalid TX request: {e}")


# =========================================================
# MAIN
# =========================================================

def main():

    sender.connect()

    start_rx_server()
    start_tx_server()

    # Start IMU producer
    start_imu(callback=broadcast)

    # Start CAN receiver
    receiver = CANReceiver(interface=CAN_INTERFACE)
    receiver.start_receiving(handle_can)


if __name__ == "__main__":
    main()
