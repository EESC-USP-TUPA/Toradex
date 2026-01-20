import os
import glob
from datetime import datetime
import logging

class DataLogger:
    def __init__(self, max_files=20, 
                 internal_dir='/datalogger', 
                 usb_dir='/usb_datalogger'):
        self.max_files = max_files
        self.internal_dir = internal_dir
        self.usb_dir = usb_dir
        self.logger = self.setup_logger()
        self.internal_file = None
        self.usb_file = None
        self.setup_data_logging()

    def setup_logger(self):
        logger = logging.getLogger('DataLogger')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def setup_directory(self, log_dir):
        os.makedirs(log_dir, exist_ok=True)
        existing_files = sorted(
            glob.glob(os.path.join(log_dir, 'can_data_*.txt')),
            key=lambda x: int(x.split('_')[-1].split('.')[0])
        )
    
        while len(existing_files) >= self.max_files:
            os.remove(existing_files.pop(0))
    
        next_num = int(existing_files[-1].split('_')[-1].split('.')[0]) + 1 if existing_files else 0
        log_path = os.path.join(log_dir, f'can_data_{next_num}.txt')
        return open(log_path, 'a'), log_path

    def setup_data_logging(self):
        self.internal_file, internal_path = self.setup_directory(self.internal_dir)
        self.logger.info(f"Criado novo arquivo de log interno: {internal_path}")

        if os.path.exists(self.usb_dir):
            self.usb_file, usb_path = self.setup_directory(self.usb_dir)
            self.logger.info(f"Criado novo arquivo de log no USB: {usb_path}")
        else:
            self.logger.warning("Diretório USB não encontrado. Logs não serão gravados no USB.")

    def process_message(self, message):
        # Formato simplificado: timestamp legível + ID + dados em hex
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Mantém milissegundos
        can_id = f"0x{message.arbitration_id:04X}"  # Formato hexadecimal com 4 dígitos
        data_hex = message.data.hex().upper()       # Dados em hexadecimal maiúsculo
        
        return {
            "timestamp": timestamp,
            "can_id": can_id,
            "raw": data_hex
        }

    def log_data(self, data):
        # Formato: [timestamp] ID:0x123 DATA:AABBCCDDEE
        log_entry = f"[{data['timestamp']}] ID:{data['can_id']} DATA:{data['raw']}"
        
        self.internal_file.write(f"{log_entry}\n")
        self.internal_file.flush()
        
        if self.usb_file:
            self.usb_file.write(f"{log_entry}\n")
            self.usb_file.flush()

    def __del__(self):
        if self.internal_file:
            self.internal_file.close()
        if self.usb_file:
            self.usb_file.close()