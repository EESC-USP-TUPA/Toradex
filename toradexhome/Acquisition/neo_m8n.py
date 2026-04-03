import serial
import threading
import time
import logging

logger = logging.getLogger("NEO-M8N")
logging.basicConfig(level=logging.INFO)

SERIAL_PORT = "/dev/ttymxc2"   # UART2
BAUDRATE = 9600


# =========================================================
# NMEA PARSER
# =========================================================

def parse_latlon(value, direction):
    if not value or not direction:
        return None

    try:
        deg_len = 2 if direction in ("N", "S") else 3

        degrees = float(value[:deg_len])
        minutes = float(value[deg_len:])

        decimal = degrees + minutes / 60.0

        if direction in ("S", "W"):
            decimal = -decimal

        return decimal

    except:
        return None


# =========================================================
# GNSS THREAD
# =========================================================

def start(callback):

    def loop():

        while True:
            try:
                logger.info(f"Opening {SERIAL_PORT} @ {BAUDRATE}")

                ser = serial.Serial(
                    SERIAL_PORT,
                    BAUDRATE,
                    timeout=1
                )

                buffer = ""

                current_data = {
                    "latitude": None,
                    "longitude": None,
                    "altitude": None,
                    "speed": 0.0,
                    "heading": 0.0,
                    "satellites": 0,
                    "fix": 0
                }

                while True:
                    data = ser.read(256).decode(errors="ignore")

                    if not data:
                        continue

                    buffer += data

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()

                        # DEBUG RAW DATA
                        print("RAW:", line)

                        # ---------------------------
                        # GGA → posição
                        # ---------------------------
                        if line.startswith("$GNGGA") or line.startswith("$GPGGA"):

                            parts = line.split(",")

                            if len(parts) < 10:
                                continue

                            current_data["latitude"] = parse_latlon(parts[2], parts[3])
                            current_data["longitude"] = parse_latlon(parts[4], parts[5])
                            current_data["fix"] = int(parts[6]) if parts[6] else 0
                            current_data["satellites"] = int(parts[7]) if parts[7] else 0
                            current_data["altitude"] = float(parts[9]) if parts[9] else 0.0

                        # ---------------------------
                        # RMC → velocidade
                        # ---------------------------
                        elif line.startswith("$GNRMC") or line.startswith("$GPRMC"):

                            parts = line.split(",")

                            if len(parts) < 9:
                                continue

                            if parts[2] != "A":
                                continue

                            speed_knots = float(parts[7]) if parts[7] else 0.0
                            current_data["speed"] = speed_knots * 0.514444
                            current_data["heading"] = float(parts[8]) if parts[8] else 0.0

                        # ---------------------------
                        # ENVIA SEM PRECISAR DE FIX
                        # ---------------------------
                        if (
                            current_data["latitude"] is not None
                            and current_data["longitude"] is not None
                        ):

                            payload = {
                                "source": "gps",
                                "timestamp_ns": time.time_ns(),
                                **current_data
                            }

                            print("SENDING:", payload)
                            callback(payload)

            except Exception as e:
                logger.error(f"GNSS error: {e}")
                time.sleep(2)

    threading.Thread(target=loop, daemon=True).start()
