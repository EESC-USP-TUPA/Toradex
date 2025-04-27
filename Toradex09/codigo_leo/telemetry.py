import paho.mqtt.client as mqtt
import json


class MyTelemetry():
    
    def __init__(self, THINGSBOARD_HOST, ACCESS_TOKEN):
        self.client = mqtt.Client()
        self.client.username_pw_set(ACCESS_TOKEN)
        self.client.connect(THINGSBOARD_HOST, 1883, 60)
        self.teste = 0
        self.telemetryData = {'temperature': 80, 'humidity': 80, 'teste' : self.teste}

    def public_on_ThingsBoard(self, data):
        self.client.publish('v1/devices/me/telemetry', json.dumps(data))




# while True:
#     telemetry = {'temperature': 22.5, 'humidity': 60}
#     client.publish('v1/devices/me/telemetry', json.dumps(telemetry))
#     print(f"Dados enviados: {telemetry}")
#     time.sleep(5)  # Envia dados a cada 5 segundos

