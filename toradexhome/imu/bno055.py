import time
import struct
from smbus2 import SMBus

BNO055_ADDRESS = 0x28

# Registers
BNO055_OPR_MODE = 0x3D
BNO055_PWR_MODE = 0x3E
BNO055_SYS_TRIGGER = 0x3F
BNO055_UNIT_SEL = 0x3B
BNO055_EULER_H_LSB = 0x1A
BNO055_CALIB_STAT = 0x35

CONFIG_MODE = 0x00
NDOF_MODE = 0x0C

def write_byte(bus, reg, value):
    bus.write_byte_data(BNO055_ADDRESS, reg, value)
    time.sleep(0.01)

def read_bytes(bus, reg, length):
    return bus.read_i2c_block_data(BNO055_ADDRESS, reg, length)

def init_bno055(bus):
    print("Initializing BNO055...")
    write_byte(bus, BNO055_OPR_MODE, CONFIG_MODE)
    time.sleep(0.05)

    write_byte(bus, BNO055_PWR_MODE, 0x00)
    time.sleep(0.01)

    write_byte(bus, BNO055_SYS_TRIGGER, 0x00)
    time.sleep(0.01)

    write_byte(bus, BNO055_UNIT_SEL, 0x00)

    write_byte(bus, BNO055_OPR_MODE, NDOF_MODE)
    time.sleep(0.1)

def read_euler(bus):
    data = read_bytes(bus, BNO055_EULER_H_LSB, 6)
    heading, roll, pitch = struct.unpack('<hhh', bytes(data))
    return heading/16.0, roll/16.0, pitch/16.0

def read_calibration(bus):
    cal = bus.read_byte_data(BNO055_ADDRESS, BNO055_CALIB_STAT)
    sys = (cal >> 6) & 0x03
    gyro = (cal >> 4) & 0x03
    accel = (cal >> 2) & 0x03
    mag = cal & 0x03
    return sys, gyro, accel, mag

def main():
    with SMBus(3) as bus:
        init_bno055(bus)

        while True:
            heading, roll, pitch = read_euler(bus)
            sys, gyro, accel, mag = read_calibration(bus)

            print(
                f"H:{heading:6.2f}°  R:{roll:6.2f}°  P:{pitch:6.2f}°  | "
                f"CAL SYS:{sys} G:{gyro} A:{accel} M:{mag}"
            )

            time.sleep(0.1)

if __name__ == "__main__":
    main()
