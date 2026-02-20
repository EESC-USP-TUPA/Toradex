import can
import logging
import threading
import time


class CANReceiver:
    """
    Handles CAN reception via socketcan.
    Automatically reconnects if bus fails.
    """

    def __init__(self, interface="can0"):
        self.interface = interface
        self.bus = None
        self.running = False
        self.logger = logging.getLogger("CANReceiver")

    # =====================================================
    # CONNECT TO CAN BUS
    # =====================================================

    def connect(self):
        try:
            self.bus = can.interface.Bus(
                interface="socketcan",
                channel=self.interface
            )
            self.logger.info(f"CAN RX connected on {self.interface}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect CAN RX: {e}")
            self.bus = None
            return False

    # =====================================================
    # START RECEIVING LOOP
    # =====================================================

    def start_receiving(self, callback):
        """
        Start blocking receive loop.
        callback(msg) will be called for each CAN frame.
        """
        self.running = True

        while self.running:

            if self.bus is None:
                if not self.connect():
                    time.sleep(2)
                    continue

            try:
                msg = self.bus.recv(timeout=1.0)

                if msg is not None:
                    callback(msg)

            except can.CanError as e:
                self.logger.error(f"CAN RX error: {e}")
                self._reset_bus()

            except Exception as e:
                self.logger.error(f"Unexpected RX error: {e}")
                self._reset_bus()

    # =====================================================
    # RESET BUS
    # =====================================================

    def _reset_bus(self):
        try:
            if self.bus:
                self.bus.shutdown()
        except:
            pass

        self.bus = None
        time.sleep(1)

    # =====================================================
    # STOP RECEIVER
    # =====================================================

    def stop(self):
        self.running = False
        self._reset_bus()

    # =====================================================
    # CLEANUP
    # =====================================================

    def shutdown(self):
        self.stop()
        self.logger.info("CAN RX shutdown")
