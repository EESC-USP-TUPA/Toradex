import os
import glob
from datetime import datetime
import logging
import csv
from collections import defaultdict

# Funções de processamento (adaptadas de Processo.py)
def process_id_0080(timestamp, data):
    """Processa mensagens com ID 0x0080"""
    if len(data) >= 8:
        apps_real = (data[0] << 8) | data[1]
        bse_real = (data[2] << 8) | data[3]
        volante = (data[4] << 8) | data[5]
        erros = data[6]
        contador = data[7]
        return [timestamp, apps_real, bse_real, volante, erros, contador]
    return None

def process_id_0090(timestamp, data):
    """Processa mensagens com ID 0x0090"""
    if len(data) >= 6:
        apps1raw = (data[0] << 8) | data[1]
        apps2raw = (data[2] << 8) | data[3]
        erros = data[4]
        contador = data[5]
        return [timestamp, apps1raw, apps2raw, erros, contador]
    return None

def process_id_0091(timestamp, data):
    """Processa mensagens com ID 0x0091"""
    if len(data) >= 7:
        bse1raw = (data[0] << 8) | data[1]
        bse2raw = (data[2] << 8) | data[3]
        volraw = (data[4] << 8) | data[5]
        contador = data[6]
        return [timestamp, bse1raw, bse2raw, volraw, contador]
    return None

def process_id_003B(timestamp, data):
    """Processa mensagens com ID 0x003B"""
    if len(data) >= 5:
        corrente_pack = data[0]
        in_use_1 = data[1]
        tensao_instantanea = data[2]
        in_use_2 = data[3]
        crc_checksum = data[4]
        return [timestamp, corrente_pack, in_use_1, tensao_instantanea, in_use_2, crc_checksum]
    return None

def process_id_03CB(timestamp, data):
    """Processa mensagens com ID 0x03CB"""
    if len(data) >= 7:
        pack_dcl = data[0]
        pack_ccl = data[1]
        blank = data[2]
        simulated_soc = data[3]
        high_temp = data[4]
        low_temp = data[5]
        crc_checksum = data[6]
        return [timestamp, pack_dcl, pack_ccl, blank, simulated_soc, high_temp, low_temp, crc_checksum]
    return None

def process_id_06B2(timestamp, data):
    """Processa mensagens com ID 0x06B2"""
    if len(data) >= 8:
        relay_state = data[0]
        pack_soc = data[1]
        pack_resistance = data[2]
        in_use_1 = data[3]
        pack_open_voltage = data[4]
        in_use_2 = data[5]
        pack_amphours = data[6]
        crc_checksum = data[7]
        return [timestamp, relay_state, pack_soc, pack_resistance, in_use_1, 
                pack_open_voltage, in_use_2, pack_amphours, crc_checksum]
    return None

# Mapeamento de IDs para funções de processamento e cabeçalhos
PROCESS_FUNCTIONS = {
    0x0080: {
        'function': process_id_0080,
        'header': ['Timestamp', 'APPS Real', 'BSE Real', 'Volante', 'Erros', 'Contador']
    },
    0x0090: {
        'function': process_id_0090,
        'header': ['Timestamp', 'apps1Raw', 'apps2Raw', 'Erros', 'Contador']
    },
    0x0091: {
        'function': process_id_0091,
        'header': ['Timestamp', 'bse1Raw', 'bse2Raw', 'volRaw', 'Contador']
    },
    0x003B: {
        'function': process_id_003B,
        'header': ['Timestamp', 'CorrentePack', 'IN_USE_1', 'TensaoInstantanea', 'IN_USE_2', 'CRC_Checksum']
    },
    0x03CB: {
        'function': process_id_03CB,
        'header': ['Timestamp', 'PackDCL', 'PackCCL', 'Blank', 'SimulatedSOC', 'HighTemp', 'LowTemp', 'CRC_Checksum']
    },
    0x06B2: {
        'function': process_id_06B2,
        'header': ['Timestamp', 'RelayState', 'PackSOC', 'PackResistance', 'IN_USE_1', 
                  'PackOpenVoltage', 'IN_USE_2', 'PackAmphours', 'CRC_Checksum']
    }
}

class DataLogger:
    def __init__(self, max_files=20, 
                 internal_dir='/datalogger', 
                 usb_dir='/usb_datalogger',
                 processed_dir='/processed_data'):
        self.max_files = max_files
        self.internal_dir = internal_dir
        self.usb_dir = usb_dir
        self.processed_dir = processed_dir
        self.logger = self.setup_logger()
        self.internal_file = None
        self.usb_file = None
        self.csv_writers = {}
        self.csv_files = {}
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

    def setup_processed_directory(self):
        """Configura o diretório para dados processados e inicializa escritores CSV"""
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Para cada ID conhecido, criar um arquivo CSV e escritor
        for can_id, info in PROCESS_FUNCTIONS.items():
            safe_id = f"{can_id:04X}"
            filename = os.path.join(self.processed_dir, f'ID_{safe_id}.csv')
            
            # Verificar se o arquivo já existe para não sobrescrever o cabeçalho
            file_exists = os.path.isfile(filename)
            
            csv_file = open(filename, 'a', newline='')
            csv_writer = csv.writer(csv_file)
            
            # Escrever cabeçalho apenas se for um novo arquivo
            if not file_exists:
                csv_writer.writerow(info['header'])
            
            self.csv_files[can_id] = csv_file
            self.csv_writers[can_id] = csv_writer

    def setup_data_logging(self):
        self.internal_file, internal_path = self.setup_directory(self.internal_dir)
        self.logger.info(f"Criado novo arquivo de log interno: {internal_path}")

        if os.path.exists(self.usb_dir):
            self.usb_file, usb_path = self.setup_directory(self.usb_dir)
            self.logger.info(f"Criado novo arquivo de log no USB: {usb_path}")
        else:
            self.logger.warning("Diretório USB não encontrado. Logs não serão gravados no USB.")
        
        # Configurar diretório para dados processados
        self.setup_processed_directory()
        self.logger.info(f"Diretório de dados processados configurado: {self.processed_dir}")

    def process_message(self, message):
        """Processa uma mensagem CAN para log bruto e processado"""
        # Formatar dados para log bruto
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        can_id = f"0x{message.arbitration_id:04X}"
        data_hex = message.data.hex().upper()
        
        # Processar dados para CSV se for um ID conhecido
        if message.arbitration_id in PROCESS_FUNCTIONS:
            processed = PROCESS_FUNCTIONS[message.arbitration_id]['function'](
                timestamp, 
                message.data
            )
            if processed:
                self.csv_writers[message.arbitration_id].writerow(processed)
                self.csv_files[message.arbitration_id].flush()
        
        return {
            "timestamp": timestamp,
            "can_id": can_id,
            "raw": data_hex
        }

    def log_data(self, data):
        """Registra dados brutos no arquivo TXT"""
        log_entry = f"[{data['timestamp']}] ID:{data['can_id']} DATA:{data['raw']}"
        
        self.internal_file.write(f"{log_entry}\n")
        self.internal_file.flush()
        
        if self.usb_file:
            self.usb_file.write(f"{log_entry}\n")
            self.usb_file.flush()

    def close_files(self):
        """Fecha todos os arquivos abertos"""
        if self.internal_file:
            self.internal_file.close()
        if self.usb_file:
            self.usb_file.close()
        for csv_file in self.csv_files.values():
            csv_file.close()

    def __del__(self):
        self.close_files()
