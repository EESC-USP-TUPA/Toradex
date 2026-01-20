import can
import logging
from time import sleep
from collections import defaultdict

# Funções de processamento
def process_id_0080(msg):
    """Processa mensagens com ID 0x0080"""
    data = msg.data
    if len(data) >= 8:
        apps_real = (data[0] << 8) | data[1]
        bse_real = (data[2] << 8) | data[3]
        volante = (data[4] << 8) | data[5]
        erros = data[6]
        contador = data[7]
        return {
            'APPS Real': apps_real,
            'BSE Real': bse_real,
            'Volante': volante,
            'Erros': erros,
            'Contador': contador
        }
    return None

def process_id_0090(msg):
    """Processa mensagens com ID 0x0090"""
    data = msg.data
    if len(data) >= 6:
        apps1raw = (data[0] << 8) | data[1]
        apps2raw = (data[2] << 8) | data[3]
        erros = data[4]
        contador = data[5]
        return {
            'apps1Raw': apps1raw,
            'apps2Raw': apps2raw,
            'Erros': erros,
            'Contador': contador
        }
    return None

def process_id_0091(msg):
    """Processa mensagens com ID 0x0091"""
    data = msg.data
    if len(data) >= 7:
        bse1raw = (data[0] << 8) | data[1]
        bse2raw = (data[2] << 8) | data[3]
        volraw = (data[4] << 8) | data[5]
        contador = data[6]
        return {
            'bse1Raw': bse1raw,
            'bse2Raw': bse2raw,
            'volRaw': volraw,
            'Contador': contador
        }
    return None

def process_id_003B(msg):
    """Processa mensagens com ID 0x003B"""
    data = msg.data
    if len(data) >= 5:
        corrente_pack = data[0]
        in_use_1 = data[1]
        tensao_instantanea = data[2]
        in_use_2 = data[3]
        crc_checksum = data[4]
        return {
            'CorrentePack': corrente_pack,
            'IN_USE_1': in_use_1,
            'TensaoInstantanea': tensao_instantanea,
            'IN_USE_2': in_use_2,
            'CRC_Checksum': crc_checksum
        }
    return None

def process_id_03CB(msg):
    """Processa mensagens com ID 0x03CB"""
    data = msg.data
    if len(data) >= 7:
        pack_dcl = data[0]
        pack_ccl = data[1]
        blank = data[2]
        simulated_soc = data[3]
        high_temp = data[4]
        low_temp = data[5]
        crc_checksum = data[6]
        return {
            'PackDCL': pack_dcl,
            'PackCCL': pack_ccl,
            'Blank': blank,
            'SimulatedSOC': simulated_soc,
            'HighTemp': high_temp,
            'LowTemp': low_temp,
            'CRC_Checksum': crc_checksum
        }
    return None

def process_id_06B2(msg):
    """Processa mensagens com ID 0x06B2"""
    data = msg.data
    if len(data) >= 8:
        relay_state = data[0]
        pack_soc = data[1]
        pack_resistance = data[2]
        in_use_1 = data[3]
        pack_open_voltage = data[4]
        in_use_2 = data[5]
        pack_amphours = data[6]
        crc_checksum = data[7]
        return {
            'RelayState': relay_state,
            'PackSOC': pack_soc,
            'PackResistance': pack_resistance,
            'IN_USE_1': in_use_1,
            'PackOpenVoltage': pack_open_voltage,
            'IN_USE_2': in_use_2,
            'PackAmphours': pack_amphours,
            'CRC_Checksum': crc_checksum
        }
    return None

# Mapeamento de IDs para funções de processamento
PROCESS_FUNCTIONS = {
    0x0080: process_id_0080,
    0x0090: process_id_0090,
    0x0091: process_id_0091,
    0x003B: process_id_003B,
    0x03CB: process_id_03CB,
    0x06B2: process_id_06B2
}

# Dicionário global para armazenar os dados processados
processed_data = defaultdict(dict)

class CANReceiver:
    def __init__(self, interface='can0', mqtt_publisher=None):
        self.interface = interface
        self.bus = None
        self.logger = logging.getLogger('CANReceiver')
        self.logger.setLevel(logging.INFO)
        self.mqtt_publisher = mqtt_publisher
        
        # Configurar handler de logging
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def connect(self):
        try:
            self.bus = can.interface.Bus(
                interface='socketcan',
                channel=self.interface
            )
            self.logger.info(f"Conectado à interface CAN: {self.interface}")
            return True
        except can.CanError as e:
            self.logger.error(f"Falha na conexão: {e}")
            return False

    def start_receiving(self):
        """Inicia o recebimento e processamento de mensagens CAN"""
        self.logger.info("Iniciando recebimento de mensagens CAN...")
        while True:
            if not self.bus and not self.connect():
                sleep(5)
                continue
            try:
                msg = self.bus.recv(timeout=1)
                if msg:
                    self.process_message(msg)
            except can.CanError as e:
                self.logger.error(f"Erro CAN: {e}")
                if self.bus:
                    self.bus.shutdown()
                self.bus = None
            except Exception as e:
                self.logger.error(f"Erro inesperado: {e}")

    def process_message(self, msg):
        """Processa uma mensagem CAN e atualiza os dados processados"""
        processor = PROCESS_FUNCTIONS.get(msg.arbitration_id)
        if processor:
            result = processor(msg)
            if result:
                # Atualiza os dados processados
                processed_data[msg.arbitration_id] = result
                self.logger.debug(f"Dados processados para ID 0x{msg.arbitration_id:04X}: {result}")
                
                # Publica imediatamente via MQTT se disponível
                if self.mqtt_publisher:
                    self.mqtt_publisher.publish(msg.arbitration_id, result)
        else:
            self.logger.debug(f"Mensagem recebida ID 0x{msg.arbitration_id:04X} não processada")

    def __del__(self):
        if self.bus:
            self.bus.shutdown()
            self.logger.info("Interface CAN encerrada")
