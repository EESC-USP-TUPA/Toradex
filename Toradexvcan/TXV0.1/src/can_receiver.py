import can
import logging
from time import sleep

class CANReceiver:
    def __init__(self, interface='can0'):
        self.interface = interface
        self.bus = None
        self.logger = logging.getLogger('CANReceiver')
        
    def connect(self):
        try:
            # Note o uso completo do namespace
            self.bus = can.interface.Bus(
                interface='socketcan',
                channel=self.interface
            )
            return True
        except can.CanError as e:  # Agora pode acessar corretamente
            self.logger.error(f"Falha na conexão: {e}") 
            return False

    # ... [restante do código] ...

    def start_receiving(self, callback):
        while True:
            if not self.bus and not self.connect():
                sleep(5)
                continue
            try:
                msg = self.bus.recv(timeout=1)
                if msg:
                    callback(msg)
            except can.CanError as e:
                self.logger.error(f"Erro CAN: {e}")
                self.bus.shutdown()
                self.bus = None

    def __del__(self):
        if self.bus:
            self.bus.shutdown()