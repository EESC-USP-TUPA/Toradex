import logging
from can_receiver import CANReceiver
from data_logger import DataLogger
import subprocess
from time import sleep

def start_candump(interface='can0'):
    subprocess.Popen(["candump", interface, "-t", "d", "-d"])

def main():
    # Inicializa componentes
    data_logger = DataLogger()
    can_receiver = CANReceiver()
    
    # Inicia candump em segundo plano
    start_candump()
    
    # Callback para processar mensagens recebidas
    def message_handler(message):
        processed = data_logger.process_message(message)
        data_logger.log_data(processed)
    
    try:
        # Inicia monitoramento CAN
        can_receiver.start_receiving(message_handler)
    except KeyboardInterrupt:
        data_logger.logger.info("Encerrando...")

if __name__ == "__main__":
    main()