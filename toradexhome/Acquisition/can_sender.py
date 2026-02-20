import can
import logging

class CANSender:
    def __init__(self, interface="can0"):
        self.interface = interface
        self.logger = logging.getLogger("CANSender")
        self.bus = None

    def connect(self):
        try:
            self.bus = can.interface.Bus(
                interface="socketcan",
                channel=self.interface
            )
            self.logger.info("CAN TX conectado")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao conectar TX: {e}")
            return False

    def send(self, arbitration_id, data):
        if not self.bus:
            if not self.connect():
                return

        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=False
        )

        try:
            self.bus.send(msg)
            self.logger.info(f"TX -> ID {hex(arbitration_id)} | {data}")
        except can.CanError as e:
            self.logger.error(f"Erro envio CAN: {e}")
