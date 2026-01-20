import logging
from can_receiver import CANReceiver
from data_logger import DataLogger
from mqtt_publisher import MQTTPublisher
import subprocess
from time import sleep
import threading

def start_candump(interface='can0'):
    subprocess.Popen(["candump", interface, "-t", "d", "-d"])

def main():
    # Inicializa componentes
    data_logger = DataLogger()
    
    # Configurar MQTT Publisher
    mqtt_publisher = MQTTPublisher(
        host='585ad9374b1f471696d5eaec9ec6a320.s1.eu.hivemq.cloud',
        port=8883,
        username='TesteTupa',
        password='Tup@2023'
    )
    
    # Conectar ao MQTT
    if not mqtt_publisher.connect():
        data_logger.logger.error("Falha na conexão MQTT. Dados não serão enviados.")
    
    # Inicia candump em segundo plano
    start_candump()
    
    # Inicializa o receiver com referência ao MQTT Publisher
    can_receiver = CANReceiver(mqtt_publisher=mqtt_publisher)
    
    # Inicia o receiver em uma thread
    receiver_thread = threading.Thread(target=can_receiver.start_receiving, daemon=True)
    receiver_thread.start()
    
    try:
        # Loop principal agora apenas mantém o programa rodando
        while True:
            sleep(1)  # Reduz uso de CPU
            
    except KeyboardInterrupt:
        data_logger.logger.info("Encerrando...")
        # Fechar arquivos no data_logger
        data_logger.close_files()
        # Desconectar MQTT
        mqtt_publisher.disconnect()

if __name__ == "__main__":
    main()
