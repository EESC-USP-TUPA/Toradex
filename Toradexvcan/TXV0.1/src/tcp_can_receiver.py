import socket
import json
import logging

class TCPCANReceiver:
    def __init__(self, host="0.0.0.0", port=5000):
        self.host = host
        self.port = port
        self.logger = logging.getLogger("TCPCANReceiver")

    def start_receiving(self, callback):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen(1)

        self.logger.info(f"🟢 Aguardando CAN via TCP na porta {self.port}")

        conn, addr = sock.accept()
        self.logger.info(f"🔗 Conectado de {addr}")

        with conn:
            while True:
                data = conn.recv(4096)
                if not data:
                    break

                messages = data.decode().splitlines()
                for line in messages:
                    msg = json.loads(line)
                    callback(self._to_can_message(msg))

    def _to_can_message(self, msg):
        class CANMessage:
            arbitration_id = int(msg["id"], 16)
            data = bytes(msg["data"])
            dlc = len(data)

        return CANMessage()
