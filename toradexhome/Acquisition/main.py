import os
import socket
import struct
import threading
import time
import logging

from can_receiver import CANReceiver
from tcp_can_receiver import TCPCANReceiver
from can_sender import CANSender


logging.basicConfig(level=logging.INFO)

CAN_INTERFACE = os.getenv("CAN_INTERFACE", "can0")
USE_TCP_INPUT = os.getenv("USE_TCP_INPUT", "0") == "1"

TX_PORT = 6000
RX_PORT = 7000

FRAME_STRUCT = struct.Struct(">IB8sQ")


class BinaryAcquisitionBridge:

    def __init__(self):
        self.clients = []
        self.sender = CANSender(interface=CAN_INTERFACE)
        self.sender.connect()

    # =====================================================
    # BROADCAST BINARY FRAME
    # =====================================================
    def broadcast(self, message):

        data = message.data.ljust(8, b'\x00')
        timestamp_ns = time.time_ns()

        packed = FRAME_STRUCT.pack(
            message.arbitration_id,
            message.dlc,
            data,
            timestamp_ns
        )

        dead_clients = []

        for conn in self.clients:
            try:
                conn.sendall(packed)
            except:
                dead_clients.append(conn)

        for c in dead_clients:
            self.clients.remove(c)

    # =====================================================
    # RX CLIENTS (binary stream)
    # =====================================================
    def start_rx_server(self):

        def server():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("0.0.0.0", RX_PORT))
            sock.listen(5)

            logging.info(f"Binary RX broadcast on {RX_PORT}")

            while True:
                conn, _ = sock.accept()
                self.clients.append(conn)

        threading.Thread(target=server, daemon=True).start()

    # =====================================================
    # TX SERVER (binary input)
    # =====================================================
    def start_tx_server(self):

        def server():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("0.0.0.0", TX_PORT))
            sock.listen(5)

            logging.info(f"Binary TX server on {TX_PORT}")

            while True:
                conn, _ = sock.accept()
                threading.Thread(
                    target=self.handle_tx_client,
                    args=(conn,),
                    daemon=True
                ).start()

        threading.Thread(target=server, daemon=True).start()

    def handle_tx_client(self, conn):

        with conn:
            while True:
                raw = conn.recv(FRAME_STRUCT.size)
                if not raw:
                    break

                arbitration_id, dlc, data, _ = FRAME_STRUCT.unpack(raw)

                self.sender.send(
                    arbitration_id,
                    data[:dlc]
                )


def main():

    bridge = BinaryAcquisitionBridge()

    bridge.start_rx_server()
    bridge.start_tx_server()

    if USE_TCP_INPUT:
        receiver = TCPCANReceiver(port=5000)
    else:
        receiver = CANReceiver(interface=CAN_INTERFACE)

    receiver.start_receiving(bridge.broadcast)


if __name__ == "__main__":
    main()
