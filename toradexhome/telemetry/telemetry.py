import socket
import json
import time
import logging
import threading
from foxglove_sender import FoxgloveSender

logging.basicConfig(level=logging.INFO)

ACQUISITION_HOST = "127.0.0.1"
ACQUISITION_PORT = 7000

CONTROL_HOST = "127.0.0.1"
CONTROL_PORT = 7001

RECONNECT_DELAY = 2

# ==========================================================
# TIME-WINDOW AGGREGATOR (20Hz)
# ==========================================================

class TimeWindowAggregator:
    def __init__(self, fox_sender, interval_sec=0.05):
        self.fox = fox_sender
        self.interval = interval_sec
        self.lock = threading.Lock()
        self.buffers = {}
        self.meta_buffers = {}
        
    def add_value(self, topic, value, unit=""):
        """Thread-safe method to dump incoming raw hardware data."""
        # Only accept numeric values for averaging
        if not isinstance(value, (int, float)):
            return
            
        with self.lock:
            if topic not in self.buffers:
                self.buffers[topic] = []
            self.buffers[topic].append(value)
            self.meta_buffers[topic] = unit

    def _flush_and_send(self):
        """Computes averages and pushes to Foxglove."""
        with self.lock:
            current_buffers = self.buffers
            self.buffers = {}
            meta = self.meta_buffers
            self.meta_buffers = {}

        timestamp = time.time_ns()

        for topic, values in current_buffers.items():
            if not values:
                continue
            
            # Calculate the average of all data points received in this window
            avg_value = sum(values) / len(values)
            unit = meta.get(topic, "")

            payload = {"value": avg_value, "timestamp_ns": timestamp}
            if unit: 
                payload["unit"] = unit

            try:
                self.fox.send_message(topic, payload)
            except Exception as e:
                logging.error(f"Failed to send averaged data for {topic}: {e}")

    def start(self):
        """Runs the 20Hz broadcast loop in the background."""
        def loop():
            while True:
                start_time = time.time()
                self._flush_and_send()
                
                # Precise sleep calculation to maintain an accurate 20Hz rhythm
                elapsed = time.time() - start_time
                sleep_time = max(0, self.interval - elapsed)
                time.sleep(sleep_time)

        threading.Thread(target=loop, daemon=True).start()

# ==========================================================
# CONNECTION HELPERS
# ==========================================================

def connect(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((host, port))
    return sock

# ==========================================================
# ACQUISITION LISTENER
# ==========================================================

def acquisition_listener(fox, aggregator):
    while True:
        try:
            logging.info("Connecting to acquisition...")
            sock = connect(ACQUISITION_HOST, ACQUISITION_PORT)
            logging.info("Connected to acquisition")

            sock_file = sock.makefile('r', encoding='utf-8')

            while True:
                line = sock_file.readline()
                
                if not line:
                    raise ConnectionError("Acquisition connection closed")

                if not line.strip():
                    continue

                try:
                    msg = json.loads(line)
                    
                    if "n" in msg and "v" in msg:
                        if msg.get("v") is not None:
                            aggregator.add_value(msg.get("n"), msg.get("v"))

                    elif msg.get("source") == "can":
                        signals = msg.get("signals", {})
                        for name, value in signals.items():
                            aggregator.add_value(f"/CAN/{name}", value)

                    '''elif msg.get("source") == "imu":
                        for signal in msg.get("signals", []):
                            name = signal.get("name")
                            value = signal.get("value")
                            if name:
                                aggregator.add_value(name, value)

                    elif msg.get("source") == "gps":
                        # Break GPS payload into individual topics for averaging
                        if "latitude" in msg and "longitude" in msg:
                            aggregator.add_value("/GPS/latitude", msg.get("latitude", 0.0))
                            aggregator.add_value("/GPS/longitude", msg.get("longitude", 0.0))
                            aggregator.add_value("/GPS/altitude", msg.get("altitude", 0.0))
                            aggregator.add_value("/GPS/speed", msg.get("speed", 0.0))
                            aggregator.add_value("/GPS/heading", msg.get("heading", 0.0))
                            aggregator.add_value("/GPS/satellites", msg.get("satellites", 0))
                            aggregator.add_value("/GPS/fix", msg.get("fix", 0))'''

                except Exception as e:
                    logging.error(f"Invalid JSON line in acquisition: {e}")

        except Exception as e:
            logging.error(f"Acquisition connection error: {e}")
            logging.info(f"Reconnecting acquisition in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)

# ==========================================================
# CONTROL LISTENER
# ==========================================================

def control_listener(fox, aggregator):
    while True:
        try:
            logging.info("Connecting to control...")
            sock = connect(CONTROL_HOST, CONTROL_PORT)
            logging.info("Connected to control")

            sock_file = sock.makefile('r', encoding='utf-8')

            while True:
                line = sock_file.readline()
                
                if not line:
                    raise ConnectionError("Control connection closed")

                if not line.strip():
                    continue

                try:
                    msg = json.loads(line)

                    # Adaptado para o mesmo padrão do acquisition_listener:
                    if "n" in msg and "v" in msg:
                        if msg.get("v") is not None:
                            # Pega o nome vindo do ControlECU
                            topic_name = msg.get("n")
                            
                            # Limpa barras duplas caso o nome original já tenha barra
                            if topic_name.startswith("/"):
                                topic_name = topic_name.lstrip("/")
                                
                            # Manda pro Foxglove agrupado dentro da "pasta" /control/
                            aggregator.add_value(f"/control/{topic_name}", msg.get("v"))

                except Exception as e:
                    logging.error(f"Invalid JSON line in control: {e}")

        except Exception as e:
            logging.error(f"Control connection error: {e}")
            logging.info(f"Reconnecting control in {RECONNECT_DELAY}s...")
            time.sleep(RECONNECT_DELAY)

# ==========================================================
# MAIN
# ==========================================================

def main():
    fox = FoxgloveSender(port=9000)
    fox.start()

    # Initialize the 20Hz (0.05 seconds) aggregator
    aggregator = TimeWindowAggregator(fox, interval_sec=0.05)
    aggregator.start()

    # Pass the aggregator down into the network listeners
    threading.Thread(target=acquisition_listener, args=(fox, aggregator), daemon=True).start()
    threading.Thread(target=control_listener, args=(fox, aggregator), daemon=True).start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()