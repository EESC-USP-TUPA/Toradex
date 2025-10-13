import logging
from can_receiver import CANReceiver, processed_data
from data_logger import DataLogger
import subprocess
from time import sleep
import threading

def start_candump(interface='can0'):
    subprocess.Popen(["candump", interface, "-t", "d", "-d"])

def main():
    # Inicializa componentes
    data_logger = DataLogger()
    can_receiver = CANReceiver()
    
    # Inicia candump em segundo plano
    start_candump()
    
    # Inicia o receiver em uma thread
    receiver_thread = threading.Thread(target=can_receiver.start_receiving, daemon=True)
    receiver_thread.start()
    
    try:
        while True:
            sleep(1)
            # Log dos dados processados (opcional)
            for can_id, data in processed_data.items():
                data_logger.logger.info(f"ID 0x{can_id:04X}: {data}")
                
    except KeyboardInterrupt:
        data_logger.logger.info("Encerrando...")
        # Fechar arquivos no data_logger
        data_logger.close_files()

if __name__ == "__main__":
    main()
