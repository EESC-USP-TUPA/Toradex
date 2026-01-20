import logging
from can_receiver import CANReceiver
from data_logger import DataLogger
# 1. Importa a nova classe
from foxglove_sender import FoxgloveSender 
import subprocess
from time import sleep

def start_candump(interface='can0'):
    try:
        subprocess.Popen(["candump", interface, "-t", "d", "-d"])
    except FileNotFoundError:
        print("Aviso: candump não encontrado, pulando...")

def main():
    # Inicializa componentes
    data_logger = DataLogger()
    can_receiver = CANReceiver()
    
    # 2. Instancia e inicia o Foxglove
    fox_sender = FoxgloveSender(port=8765)
    fox_sender.start()
    
    # Inicia candump em segundo plano
    start_candump()
    
    # Callback para processar mensagens recebidas
    def message_handler(message):
        # A. Salva no disco (CSV/TXT)
        processed = data_logger.process_message(message)
        data_logger.log_data(processed)
        
        # B. Envia para o PC via Foxglove (EM TEMPO REAL)
        fox_sender.send_message(message)
    
    try:
        # Inicia monitoramento CAN
        can_receiver.start_receiving(message_handler)
    except KeyboardInterrupt:
        data_logger.logger.info("Encerrando...")

if __name__ == "__main__":
    main()