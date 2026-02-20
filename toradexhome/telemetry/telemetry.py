import time
import random
import foxglove
from foxglove import Channel

foxglove.set_log_level("INFO")

# Start server on 0.0.0.0:8765
foxglove.start_server(host="0.0.0.0", port=8765)

# JSON channel for pack voltage
voltage_channel = Channel("/pack/voltage", message_encoding="json")

print("Server running on ws://0.0.0.0:8765, logging /pack/voltage.v")

while True:
    v = 380.0 + 5.0*(random.random() - 0.5)
    print("sending", v)
    voltage_channel.log({"v": v})   # <-- message has a single field 'v'
    time.sleep(0.05)                # 20 Hz

