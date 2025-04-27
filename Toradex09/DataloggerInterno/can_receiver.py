import can
import os
import logging
import subprocess
import glob
import json
from time import sleep, time

class CANMonitor:
    def __init__(self, interface='can0', max_files=20):
        self.interface = interface
        self.max_files = max_files
        self.logger = self.setup_logger()
        self.bus = None
        self.log_file = None
        self.current_log_path = None
        self.setup_data_logging()

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
        """Manage log files with rotation"""
        log_dir = '/datalogger'
        os.makedirs(log_dir, exist_ok=True)
        
        existing_files = sorted(
            glob.glob(os.path.join(log_dir, 'can_data_*.txt')),
            key=lambda x: int(x.split('_')[-1].split('.')[0])
        )
        
        while len(existing_files) >= self.max_files:
            os.remove(existing_files.pop(0))
        
        next_num = int(existing_files[-1].split('_')[-1].split('.')[0]) + 1 if existing_files else 0
        self.current_log_path = os.path.join(log_dir, f'can_data_{next_num}.txt')
        self.log_file = open(self.current_log_path, 'a')
        self.logger.info(f"Created new log file: {self.current_log_path}")

    def process_can_message(self, message, data):
        """Process specific CAN IDs into structured data"""
        data.update({
            "timestamp": time(),
            "can_id": f"0x{message.arbitration_id:X}"
        })
        
        # 0x080 - Vehicle Control
        if message.arbitration_id == 0x080:
            if len(message.data) >= 7:
                data.update({
                    "AccelPedal": message.data[0] | (message.data[1] << 8),
                    "BrakePedal": message.data[2] | (message.data[3] << 8),
                    "SteerAngle": message.data[4] | (message.data[5] << 8),
                    "Flags": message.data[6]
                })
        
        # 0x081 - System Status
        elif message.arbitration_id == 0x081:
            if len(message.data) >= 2:
                data.update({
                    "InterruptBtn": message.data[0],
                    "InvShutdown": message.data[1]
                })
        
        # 0x180 - Left Wheel Sensors
        elif message.arbitration_id == 0x180:
            if len(message.data) >= 8:
                data.update({
                    "APPS2_L": message.data[0] | (message.data[1] << 8),
                    "Susp_L": message.data[2] | (message.data[3] << 8),
                    "WheelRPM_L": message.data[4] | (message.data[5] << 8),
                    "BrakeTemp_L": message.data[6] | (message.data[7] << 8)
                })
        
        # 0x181 - Left Pitot Sensor
        elif message.arbitration_id == 0x181:
            if len(message.data) >= 2:
                data["Pitot_L"] = message.data[0] | (message.data[1] << 8)
        
        # 0x280 - Right Wheel Sensors
        elif message.arbitration_id == 0x280:
            if len(message.data) >= 8:
                data.update({
                    "APPS2_R": message.data[0] | (message.data[1] << 8),
                    "Susp_R": message.data[2] | (message.data[3] << 8),
                    "WheelRPM_R": message.data[4] | (message.data[5] << 8),
                    "BrakeTemp_R": message.data[6] | (message.data[7] << 8)
                })
        
        # 0x281 - Right Pitot Sensor
        elif message.arbitration_id == 0x281:
            if len(message.data) >= 2:
                data["Pitot_R"] = message.data[0] | (message.data[1] << 8)
        
        # 0x050 - Inverter Status
        elif message.arbitration_id == 0x050:
            if len(message.data) >= 6:
                data.update({
                    "Inv_SW_L": message.data[0],
                    "Inv_SW_R": message.data[1],
                    "Inv_AN_L": message.data[2],
                    "Inv_AN_R": message.data[3],
                    "BuzzerFlag": message.data[4],
                    "BreaklightFlag": message.data[5]
                })
        
        # 0x380 - Rear Left Motor
        elif message.arbitration_id == 0x380:
            if len(message.data) >= 6:
                data.update({
                    "MotorRPM1_BL": message.data[0] | (message.data[1] << 8),
                    "WheelRPM_BL": message.data[2] | (message.data[3] << 8),
                    "Susp_BL": message.data[4] | (message.data[5] << 8)
                })
        
        # 0x381 - Rear Left Temperatures
        elif message.arbitration_id == 0x381:
            if len(message.data) >= 5:
                data.update({
                    "MotorTemp2_BL": message.data[0],
                    "InvTemp2_BL": message.data[1],
                    "TransTemp2_BL": message.data[2],
                    "BrakeTemp4_BL": message.data[3] | (message.data[4] << 8)
                })
        
        # 0x382 - Rear Left GPS
        elif message.arbitration_id == 0x382:
            data["GPS_BL"] = message.data.hex()
        
        # 0x480 - Rear Right Motor
        elif message.arbitration_id == 0x480:
            if len(message.data) >= 6:
                data.update({
                    "MotorRPM2_BR": message.data[0] | (message.data[1] << 8),
                    "WheelRPM_BR": message.data[2] | (message.data[3] << 8),
                    "Susp_BR": message.data[4] | (message.data[5] << 8)
                })
        
        # 0x481 - Rear Right Temperatures
        elif message.arbitration_id == 0x481:
            if len(message.data) >= 5:
                data.update({
                    "MotorTemp2_BR": message.data[0],
                    "InvTemp2_BR": message.data[1],
                    "TransTemp2_BR": message.data[2],
                    "BrakeTemp4_BR": message.data[3] | (message.data[4] << 8)
                })
        
        # 0x482/0x484 - Accelerometers
        elif message.arbitration_id == 0x482:
            data["Accel1_BR"] = list(message.data[:6])
        elif message.arbitration_id == 0x484:
            data["Accel2_BR"] = list(message.data[:6])
        
        # Unprocessed IDs
        else:
            data["raw"] = message.data.hex()

    def start_candump(self):
        subprocess.Popen(["candump", self.interface, "-t", "d", "-d"])

    def connect(self):
        try:
            self.bus = can.interface.Bus(
                interface='socketcan',
                channel=self.interface
            )
            return True
        except can.CanError as e:
            self.logger.error(f"Connection failed: {e}")
            return False

    def monitor(self):
        self.start_candump()
        while True:
            if not self.bus and not self.connect():
                sleep(5)
                continue

            try:
                msg = self.bus.recv(timeout=1)
                if msg:
                    data = {}
                    self.process_can_message(msg, data)
                    
                    if "raw" not in data:
                        log_entry = json.dumps(data)
                    else:
                        log_entry = f"ID:{data['can_id']} DATA:{data['raw']}"
                    
                    self.log_file.write(f"{log_entry}\n")
                    self.log_file.flush()
                    
            except can.CanError as e:
                self.logger.error(f"CAN error: {e}")
                self.bus.shutdown()
                self.bus = None

    def __del__(self):
        if self.log_file:
            self.log_file.close()

if __name__ == "__main__":
    monitor = CANMonitor()
    try:
        monitor.monitor()
    except KeyboardInterrupt:
        monitor.logger.info("Shutting down...")