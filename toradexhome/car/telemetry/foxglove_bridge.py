import os
import socket
import json
import foxglove
from foxglove import Channel

SOCKET_PATH = "/shared/telemetry.sock"

foxglove.set_log_level("INFO")
foxglove.start_server(host="0.0.0.0", port=8765)

print("Foxglove running at ws://0.0.0.0:8765")

# We dynamically create channels
channels = {}

def get_channel(topic):
    if topic not in channels:
        print(f"[Foxglove] Creating channel {topic}")
        channels[topic] = Channel(topic, message_encoding="json")
    return channels[topic]

# remove old socket if exists
if os.path.exists(SOCKET_PATH):
    os.remove(SOCKET_PATH)

server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
server.bind(SOCKET_PATH)
server.listen(10)

print("Telemetry socket ready:", SOCKET_PATH)

while True:
    conn, _ = server.accept()
    print("Container connected to telemetry")

    buffer = ""

    while True:
        try:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode()

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)

                if not line.strip():
                    continue

                try:
                    msg = json.loads(line)

                    topic = msg["topic"]
                    payload = msg["data"]

                    ch = get_channel(topic)
                    ch.log(payload)

                except Exception as e:
                    print("Bad message:", e, line)

        except:
            break

    conn.close()
    print("Container disconnected")
