from collections import deque
from datetime import datetime


# ======================================================
# CONFIGURAÇÃO
# ======================================================

WINDOW_SIZE = 3  # ← quantidade dos últimos dados


class MediaMovelProcessor:
    def __init__(self, foxglove_sender):
        self.foxglove = foxglove_sender
        self.buffers = {}  # signal_name -> deque

    # ======================================================
    # PROCESSA SINAL DECODIFICADO
    # ======================================================

    def process_signal(self, signal):
        name = signal["name"]
        value = signal["value"]
        unit = signal["unit"]
        timestamp_ns = signal["timestamp_ns"]

        # Inicializa buffer do sinal
        if name not in self.buffers:
            self.buffers[name] = deque(maxlen=WINDOW_SIZE)

        buffer = self.buffers[name]
        buffer.append(value)

        # Calcula média dos últimos N valores
        avg = sum(buffer) / len(buffer)

        # Horário humano
        time_human = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Envia para o Foxglove
        self.foxglove.send_message(
            f"/AVG{name}",
            {
                "value": round(avg, 3),
                "unit": unit,
                "timestamp_ns": timestamp_ns,  # mantém Unix
                "time_human": time_human       # ← horário real
            }
        )
