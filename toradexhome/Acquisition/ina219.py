from ina219 import INA219
import logging

logger = logging.getLogger("INA219")

class INA219Reader:
    def __init__(self, bus=3, address=0x40, shunt_ohms=0.01):
        self.bus = bus
        self.address = address
        self.shunt = shunt_ohms

        self.ina = INA219(
            self.shunt,
            address=self.address,
            busnum=self.bus
        )

        try:
            self.ina.configure()
            logger.info("INA219 initialized successfully")
        except Exception as e:
            logger.error(f"INA219 init error: {e}")

    def read(self):
        try:
            voltage = self.ina.voltage()            # V
            current = self.ina.current() / 1000.0   # A
            power = self.ina.power() / 1000.0       # W

            return {
                "voltage": voltage,
                "current": current,
                "power": power
            }

        except Exception as e:
            logger.error(f"INA219 read error: {e}")
            return None
