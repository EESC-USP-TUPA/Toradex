import serial
import threading
import time
import logging

logger = logging.getLogger("NEO-M8N")

SERIAL_PORT = "/dev/ttymxc1"
BAUDRATE = 9600


# =========================================================
# NMEA LAT/LON CONVERSION (CORRECT)
# =========================================================

def parse_latlon(value, direction):
    if not value:
        return None

    # Latitude uses 2 digits for degrees, longitude uses 3
    if direction in ("N", "S"):
        deg_len = 2
    else:
        deg_len = 3

    degrees = float(value[:deg_len])
    minutes = float(value[deg_len:])

    decimal = degrees + minutes / 60.0

    if direction in ("S", "W"):
        decimal = -decimal

    return decimal


# =========================================================
# GNSS THREAD (NMEA MODE)
# =========================================================

def start(callback):

    def loop():

        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
        logger.info("GNSS running in NMEA mode @9600")

        current_data = {
            "latitude": None,
            "longitude": None,
            "altitude": 0.0,
            "speed": 0.0,
            "heading": 0.0,
            "satellites": 0,
            "fix": 0
        }

        while True:

            try:
                line = ser.readline().decode(errors="ignore").strip()

                # ---------------------------
                # GGA → position + fix + sats
                # ---------------------------
                if line.startswith("$GNGGA") or line.startswith("$GPGGA"):

                    parts = line.split(",")

                    if len(parts) < 10:
                        continue

                    lat = parse_latlon(parts[2], parts[3])
                    lon = parse_latlon(parts[4], parts[5])

                    fix = int(parts[6]) if parts[6] else 0
                    sats = int(parts[7]) if parts[7] else 0
                    alt = float(parts[9]) if parts[9] else 0.0

                    current_data["latitude"] = lat
                    current_data["longitude"] = lon
                    current_data["altitude"] = alt
                    current_data["satellites"] = sats
                    current_data["fix"] = fix

                # ---------------------------
                # RMC → speed + heading
                # ---------------------------
                elif line.startswith("$GNRMC") or line.startswith("$GPRMC"):

                    parts = line.split(",")

                    if len(parts) < 9:
                        continue

                    status = parts[2]
                    if status != "A":  # A = valid
                        continue

                    speed_knots = float(parts[7]) if parts[7] else 0.0
                    heading = float(parts[8]) if parts[8] else 0.0

                    speed_ms = speed_knots * 0.514444

                    current_data["speed"] = speed_ms
                    current_data["heading"] = heading

                # ---------------------------
                # Broadcast if valid fix
                # ---------------------------
                if (
                    current_data["fix"] > 0
                    and current_data["latitude"] is not None
                    and current_data["longitude"] is not None
                ):

                    payload = {
                        "source": "gps",
                        "timestamp_ns": time.time_ns(),
                        "latitude": current_data["latitude"],
                        "longitude": current_data["longitude"],
                        "altitude": current_data["altitude"],
                        "speed": current_data["speed"],
                        "heading": current_data["heading"],
                        "satellites": current_data["satellites"],
                        "fix": current_data["fix"]
                    }

                    callback(payload)

            except Exception as e:
                logger.error(f"GNSS error: {e}")

    threading.Thread(target=loop, daemon=True).start()
