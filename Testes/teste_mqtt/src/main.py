#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import time
import sys
import logging

# Configuração de logging para mostrar mensagens no console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Configurações MQTT baseadas no seu comando
MQTT_BROKER = "node02.myqtthub.com"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "ENVIA"
MQTT_USERNAME = "Tupa"
MQTT_PASSWORD = "tupa2023"
MQTT_TOPIC = "message/topic/to/subscribe"
MQTT_MESSAGE = "hello world"

def on_connect(client, userdata, flags, rc):
    """Callback chamado quando conectado ao broker"""
    if rc == 0:
        logger.info(f"Conectado com sucesso ao broker MQTT: {MQTT_BROKER}")
    else:
        logger.error(f"Falha na conexão. Código de retorno: {rc}")

def on_publish(client, userdata, mid):
    """Callback chamado quando uma mensagem é publicada"""
    logger.info(f"Mensagem publicada com sucesso! Message ID: {mid}")

def main():
    logger.info("Iniciando cliente MQTT...")
    
    # Configuração do cliente
    client = mqtt.Client(client_id=MQTT_CLIENT_ID, protocol=mqtt.MQTTv311)
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    # Configura callbacks
    client.on_connect = on_connect
    client.on_publish = on_publish
    
    try:
        # Conecta ao broker
        logger.info(f"Conectando ao broker: {MQTT_BROKER}:{MQTT_PORT}")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Inicia loop de rede
        client.loop_start()
        
        # Espera conexão ser estabelecida
        time.sleep(1)
        
        # Publica mensagem
        logger.info(f"Publicando mensagem: [Tópico: {MQTT_TOPIC}] [Mensagem: {MQTT_MESSAGE}]")
        result = client.publish(MQTT_TOPIC, MQTT_MESSAGE, qos=0)
        
        # Espera confirmação de publicação
        result.wait_for_publish()
        time.sleep(1)  # Garante tempo para callback
        
        # Desconecta
        client.disconnect()
        client.loop_stop()
        logger.info("Conexão encerrada")
        
    except Exception as e:
        logger.error(f"Erro durante operação MQTT: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
    logger.info("Script finalizado com sucesso!")
    sys.exit(0)
