import socket
import json
import time
import random

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("192.168.43.218", 5000))

# Estado inicial próximo do meio
data = [120 + random.randint(-3, 3) for _ in range(8)]

def next_value(v, center=120):
    """
    Gera o próximo valor com:
    - variação pequena
    - tendência leve ao centro
    - eventos ocasionais suaves
    """
    # ruído pequeno normal
    delta = random.choice([-2, -1, 0, 1, 2])

    # tendência ao centro
    if v > center:
        delta -= 1
    elif v < center:
        delta += 1

    # evento raro (subida ou queda suave)
    if random.random() < 0.01:  # 1% das vezes
        delta += random.choice([-3, 3])

    v_new = v + delta

    # limita em byte CAN
    return max(0, min(255, v_new))

while True:
    # atualiza todos os bytes
    data = [next_value(v) for v in data]

    msg = {
        "id": "0x003B",
        "data": data
    }

    sock.sendall((json.dumps(msg) + "\n").encode())
    time.sleep(0.02)
