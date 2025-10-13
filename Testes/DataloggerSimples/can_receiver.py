import can
import os
import logging
import subprocess
import glob
from time import sleep

class CANMonitor:
    def __init__(self, interface='can0'):
        self.interface = interface
        self.logger = self.setup_logger()
        self.bus = None
        self.log_file = self.setup_data_logging()

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

    def setup_data_logging(self):
        """Initialize data logging directory and file"""
        log_dir = '/datalogger'
        os.makedirs(log_dir, exist_ok=True)
        
        # Find highest existing file number
        existing_files = glob.glob(os.path.join(log_dir, 'can_data_*.txt'))
        file_numbers = [int(f.split('_')[-1].split('.')[0]) for f in existing_files if f.split('_')[-1].split('.')[0].isdigit()]
        next_num = max(file_numbers) + 1 if file_numbers else 0
        
        log_path = os.path.join(log_dir, f'can_data_{next_num}.txt')
        self.logger.info(f"Creating new log file: {log_path}")
        return open(log_path, 'a')  # Open in append mode

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
                    log_entry = f"ID:0x{msg.arbitration_id:X} DATA:{msg.data.hex()}"
                    self.logger.info(log_entry)
                    # Write to log file
                    self.log_file.write(f"{log_entry}\n")
                    self.log_file.flush()
            except can.CanError as e:
                self.logger.error(f"CAN error: {str(e)}")
                self.bus.shutdown()
                self.bus = None

if __name__ == "__main__":
    monitor = CANMonitor()
    try:
        monitor.monitor()
    finally:
        monitor.log_file.close()
