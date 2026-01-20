import can
import os
import logging
import subprocess
from time import sleep

class CANMonitor:
    def __init__(self, interface='can0'):
        self.interface = interface
        self.logger = self.setup_logger()
        self.bus = None

    def setup_logger(self):
        logger = logging.getLogger('CANMonitor')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def start_candump(self):
        """Run candump in background for verification"""
        self.logger.info("Starting candump in background...")
        subprocess.Popen([
            "candump", 
            self.interface,
            "-t", "d",
            "-d"
        ])

    def connect(self):
        self.logger.info(f"Connecting to {self.interface}")
        try:
            self.bus = can.interface.Bus(
                channel=self.interface,
                bustype='socketcan'
            )
            return True
        except can.CanError as e:
            self.logger.error(f"Connection failed: {str(e)}")
            return False

    def monitor(self):
        self.start_candump()
        while True:
            if not self.bus and not self.connect():
                self.logger.warning("Retrying connection in 5s...")
                sleep(5)
                continue

            try:
                msg = self.bus.recv(timeout=1)
                if msg:
                    self.logger.info(
                        f"ID:0x{msg.arbitration_id:X} "
                        f"DATA:{msg.data.hex()}"
                    )
            except can.CanError as e:
                self.logger.error(f"CAN error: {str(e)}")
                self.bus.shutdown()
                self.bus = None

if __name__ == "__main__":
    monitor = CANMonitor()
    monitor.monitor()