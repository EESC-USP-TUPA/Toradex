import time
import struct
import logging
from smbus2 import SMBus

BNO055_ADDRESS = 0x28

BNO055_OPR_MODE = 0x3D
BNO055_PWR_MODE = 0x3E
BNO055_SYS_TRIGGER = 0x3F
BNO055_UNIT_SEL = 0x3B
BNO055_EULER_H_LSB = 0x1A
BNO055_CALIB_STAT = 0x35

CONFIG_MODE = 0x00
NDOF_MODE = 0x0C

logger = logging.getLogger("BNO055")


def write_byte(bus, reg, value):
    bus.write_byte_data(BNO055_ADDRESS, reg, value)
    time.sleep(0.01)


def read_bytes(bus, reg, length):
    return bus.read_i2c_block_data(BNO055_ADDRESS, reg, length)


def init_bno055(bus):
    write_byte(bus, BNO055_OPR_MODE, CONFIG_MODE)
    time.sleep(0.05)

    write_byte(bus, BNO055_PWR_MODE, 0x00)
    write_byte(bus, BNO055_SYS_TRIGGER, 0x00)
    write_byte(bus, BNO055_UNIT_SEL, 0x00)

    write_byte(bus, BNO055_OPR_MODE, NDOF_MODE)
    time.sleep(0.1)


def read_euler(bus):
    data = read_bytes(bus, BNO055_EULER_H_LSB, 6)
    heading, roll, pitch = struct.unpack('<hhh', bytes(data))
    return heading / 16.0, roll / 16.0, pitch / 16.0


def read_calibration(bus):
    cal = bus.read_byte_data(BNO055_ADDRESS, BNO055_CALIB_STAT)
    sys = (cal >> 6) & 0x03
    gyro = (cal >> 4) & 0x03
    accel = (cal >> 2) & 0x03
    mag = cal & 0x03
    return sys, gyro, accel, mag


# =========================================================
# START IMU LOOP
# =========================================================

def start(callback, i2c_bus=3):

    def imu_loop():
        with SMBus(i2c_bus) as bus:

            init_bno055(bus)
            logger.info("BNO055 initialized")

            while True:
                try:
                    heading, roll, pitch = read_euler(bus)
                    sys, gyro, accel, mag = read_calibration(bus)

                    payload = {
                        "source": "imu",
                        "timestamp_ns": time.time_ns(),
                        "signals": [
                            {"name": "/IMU/heading", "value": heading, "unit": "deg"},
                            {"name": "/IMU/roll", "value": roll, "unit": "deg"},
                            {"name": "/IMU/pitch", "value": pitch, "unit": "deg"},
                            {"name": "/IMU/cal_sys", "value": sys, "unit": ""},
                            {"name": "/IMU/cal_gyro", "value": gyro, "unit": ""},
                            {"name": "/IMU/cal_accel", "value": accel, "unit": ""},
                            {"name": "/IMU/cal_mag", "value": mag, "unit": ""}
                        ]
                    }

                    callback(payload)

                    time.sleep(0.1)

                except Exception as e:
                    logger.error(f"IMU error: {e}")
                    time.sleep(1)

    import threading
    threading.Thread(target=imu_loop, daemon=True).start()
