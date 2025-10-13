import paho.mqtt.client as mqtt
import json
import logging
import ssl

class MQTTPublisher:
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.client = mqtt.Client()
        self.logger = logging.getLogger('MQTTPublisher')
        self.setup_logging()
        
        # Configurar TLS
        self.client.tls_set(tls_version=ssl.PROTOCOL_TLS)
        self.client.tls_insecure_set(True)  # Aceita certificados autoassinados
        
        # Autenticação
        self.client.username_pw_set(username, password)
        
        # Callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        
    def setup_logging(self):
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.logger.info("Conectado ao broker MQTT com sucesso!")
        else:
            self.logger.error(f"Falha na conexão MQTT. Código: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        self.logger.warning(f"Desconectado do broker MQTT. Código: {rc}")
        
    def connect(self):
        try:
            self.logger.info(f"Conectando ao broker MQTT em {self.host}:{self.port}")
            self.client.connect(self.host, self.port, 60)
            self.client.loop_start()
            return True
        except Exception as e:
            self.logger.error(f"Erro na conexão MQTT: {e}")
            return False
            
    def publish(self, can_id, data):
        try:
            # Criar tópico baseado no ID CAN
            topic = f"can/ID_{can_id:04X}"
            
            # Converter dados para JSON
            payload = json.dumps(data)
            
            # Publicar
            result = self.client.publish(topic, payload)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Dados publicados em {topic}: {payload}")
                return True
            else:
                self.logger.warning(f"Falha ao publicar em {topic}. Código: {result.rc}")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao publicar dados: {e}")
            return False
            
    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.logger.info("Conexão MQTT encerrada")
