import os
import glob
from datetime import datetime
from zoneinfo import ZoneInfo
import logging


class DataLogger:
    def __init__(self, max_folders=100, 
                 internal_dir='/datalogger'):
        self.max_folders = max_folders
        self.internal_dir = internal_dir
        self.logger = self.setup_logger()
        self.session_dir = None
        self.file_handles = {}  # Dicionário para armazenar file handles por CAN ID
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
        """Cria uma pasta com o timestamp da primeira mensagem"""
        os.makedirs(self.internal_dir, exist_ok=True)
        
        # Limpa pastas antigas se exceder o limite
        existing_dirs = sorted(
            glob.glob(os.path.join(self.internal_dir, '20*')),  # Pastas que começam com ano
            key=os.path.getctime
        )
        
        while len(existing_dirs) >= self.max_folders:
            import shutil
            shutil.rmtree(existing_dirs.pop(0))
            self.logger.info(f"Pasta antiga removida para manter limite de {self.max_folders}")
        
        # Cria nova pasta com timestamp
        timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d_%H-%M-%S")
        self.session_dir = os.path.join(self.internal_dir, timestamp)
        os.makedirs(self.session_dir, exist_ok=True)
        
        self.logger.info(f"Criada nova pasta de sessão: {self.session_dir}")


    def get_file_handle(self, can_id):
        """Retorna o file handle para um CAN ID específico, criando se necessário"""
        if can_id not in self.file_handles:
            # Remove o '0x' e formata o ID
            id_hex = can_id.replace('0x', '')
            file_path = os.path.join(self.session_dir, f"{id_hex}.txt")
            self.file_handles[can_id] = open(file_path, 'a')
            self.logger.info(f"Criado arquivo para CAN ID {can_id}: {file_path}")
        
        return self.file_handles[can_id]


    def process_message(self, message):
        """Processa mensagem CAN e retorna dados formatados"""
        # Cria pasta de sessão na primeira mensagem
        if self.first_message:
            self.setup_session_directory()
            self.first_message = False
        
        # Timestamp com timezone de Brasília (UTC-3)
        timestamp = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        # CAN ID em hexadecimal
        can_id = f"0x{message.arbitration_id:04X}"
        
        # Converte cada byte para decimal (formato: 001 255 128, etc)
        data_decimal = ' '.join(f"{byte:03d}" for byte in message.data)
        
        return {
            "timestamp": timestamp,
            "can_id": can_id,
            "raw": data_decimal
        }


    def log_data(self, data):
        """Salva dados no arquivo correspondente ao CAN ID"""
        # Formato: [timestamp] DATA:001 003 045 250 202 101 203 165
        log_entry = f"[{data['timestamp']}] {data['raw']}"
        
        # Obtém o arquivo correspondente ao CAN ID
        file_handle = self.get_file_handle(data['can_id'])
        file_handle.write(f"{log_entry}\n")
        file_handle.flush()


    def __del__(self):
        """Fecha todos os arquivos abertos"""
        for file_handle in self.file_handles.values():
            if file_handle:
                file_handle.close()
