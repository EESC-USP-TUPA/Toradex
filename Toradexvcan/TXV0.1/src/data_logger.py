import os
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

def can_int8(value):
    """Converte byte CAN para inteiro com sinal"""
    return value - 256 if value > 127 else value


class DataLogger:
    def __init__(self, max_folders=100, internal_dir='/datalogger'):
        self.max_folders = max_folders
        self.internal_dir = internal_dir
        self.logger = self.setup_logger()
        self.session_dir = None
        self.file_handles = {}
        self.first_message = True


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


    def setup_session_directory(self):
        os.makedirs(self.internal_dir, exist_ok=True)

        existing_dirs = sorted(
            glob.glob(os.path.join(self.internal_dir, '20*')),
            key=os.path.getctime
        )

        while len(existing_dirs) >= self.max_folders:
            import shutil
            shutil.rmtree(existing_dirs.pop(0))
            self.logger.info("Pasta antiga removida")

        timestamp = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).strftime("%Y-%m-%d_%H-%M-%S")

        self.session_dir = os.path.join(self.internal_dir, timestamp)
        os.makedirs(self.session_dir, exist_ok=True)

        self.logger.info(f"Criada nova pasta de sessão: {self.session_dir}")


    def get_file_handle(self, can_id):
        if can_id not in self.file_handles:
            id_hex = can_id.replace('0x', '')
            file_path = os.path.join(self.session_dir, f"{id_hex}.txt")
            self.file_handles[can_id] = open(file_path, 'a')
            self.logger.info(f"Criado arquivo para CAN ID {can_id}")

        return self.file_handles[can_id]


    def process_message(self, message):
        if self.first_message:
            self.setup_session_directory()
            self.first_message = False

        timestamp = datetime.now(
            ZoneInfo("America/Sao_Paulo")
        ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        can_id = f"0x{message.arbitration_id:04X}"

        # ===== CORREÇÃO AQUI =====
        data_list = []

        for i, byte in enumerate(message.data):
            if i == 0:
                # Byte 0 = corrente (SIGNED)
                data_list.append(f"{can_int8(byte):+04d}")
            else:
                # Outros bytes = unsigned
                data_list.append(f"{byte:03d}")

        data_decimal = ' '.join(data_list)

        return {
            "timestamp": timestamp,
            "can_id": can_id,
            "raw": data_decimal
        }


    def log_data(self, data):
        log_entry = f"[{data['timestamp']}] {data['raw']}"
        file_handle = self.get_file_handle(data['can_id'])
        file_handle.write(f"{log_entry}\n")
        file_handle.flush()


    def __del__(self):
        for file_handle in self.file_handles.values():
            if file_handle:
                file_handle.close()
