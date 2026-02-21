import time
import struct
import logging
import threading
from smbus2 import SMBus

BNO055_ADDRESS = 0x28

# Registers
BNO055_OPR_MODE = 0x3D
BNO055_PWR_MODE = 0x3E
BNO055_SYS_TRIGGER = 0x3F
BNO055_UNIT_SEL = 0x3B

REG_GYRO = 0x14
REG_LINEAR_ACCEL = 0x28
REG_EULER = 0x1A

CONFIG_MODE = 0x00
IMUPLUS_MODE = 0x08  # Lower latency than NDOF

logger = logging.getLogger("BNO055")


# =========================================================
# Low-level helpers
# =========================================================

def write_byte(bus, reg, value):
    bus.write_byte_data(BNO055_ADDRESS, reg, value)
    time.sleep(0.01)


def read_vector(bus, reg):
    data = bus.read_i2c_block_data(BNO055_ADDRESS, reg, 6)
    x, y, z = struct.unpack('<hhh', bytes(data))
    return x, y, z


# =========================================================
# Initialization
# =========================================================

def init_bno055(bus):

    write_byte(bus, BNO055_OPR_MODE, CONFIG_MODE)
    time.sleep(0.05)

    write_byte(bus, BNO055_PWR_MODE, 0x00)
    write_byte(bus, BNO055_SYS_TRIGGER, 0x00)

    # Units:
    # Accel → m/s²
    # Gyro → deg/s
    # Euler → degrees
    write_byte(bus, BNO055_UNIT_SEL, 0x00)

    write_byte(bus, BNO055_OPR_MODE, IMUPLUS_MODE)
    time.sleep(0.1)


# =========================================================
# START IMU LOOP (200 Hz Stable)
# =========================================================

def start(callback, i2c_bus=3, rate_hz=200):

    period = 1.0 / rate_hz

    def imu_loop():

        with SMBus(i2c_bus) as bus:

            init_bno055(bus)
            logger.info(f"BNO055 IMUPLUS running at {rate_hz} Hz")

            next_time = time.perf_counter()

            while True:

                try:
                    timestamp = time.time_ns()

                    # ===============================
                    # Euler (1 LSB = 1/16 deg)
                    # ===============================
                    h, r, p = read_vector(bus, REG_EULER)
                    heading = h / 16.0
                    roll = r / 16.0
                    pitch = p / 16.0

                    # ===============================
                    # Gyro (1 LSB = 1/16 deg/s)
                    # ===============================
                    gx, gy, gz = read_vector(bus, REG_GYRO)
                    gx /= 16.0
                    gy /= 16.0
                    gz /= 16.0

                    # ===============================
                    # Linear Accel (1 LSB = 1 mg)
                    # ===============================
                    ax, ay, az = read_vector(bus, REG_LINEAR_ACCEL)
                    ax /= 100.0
                    ay /= 100.0
                    az /= 100.0

                    payload = {
                        "source": "imu",
                        "timestamp_ns": timestamp,
                        "signals": [

                            # Euler
                            {"name": "/IMU/heading", "value": heading, "unit": "deg"},
                            {"name": "/IMU/roll", "value": roll, "unit": "deg"},
                            {"name": "/IMU/pitch", "value": pitch, "unit": "deg"},

                            # Gyro
                            {"name": "/IMU/gyro_x", "value": gx, "unit": "deg/s"},
                            {"name": "/IMU/gyro_y", "value": gy, "unit": "deg/s"},
                            {"name": "/IMU/gyro_z", "value": gz, "unit": "deg/s"},

                            # Linear acceleration
                            {"name": "/IMU/lin_accel_x", "value": ax, "unit": "m/s²"},
                            {"name": "/IMU/lin_accel_y", "value": ay, "unit": "m/s²"},
                            {"name": "/IMU/lin_accel_z", "value": az, "unit": "m/s²"},
                        ]
                    }

                    callback(payload)

                except Exception as e:
                    logger.error(f"IMU error: {e}")

                # ===============================
                # Deterministic timing control
                # ===============================
                next_time += period
                sleep_time = next_time - time.perf_counter()

                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    next_time = time.perf_counter()

    threading.Thread(target=imu_loop, daemon=True).start()
