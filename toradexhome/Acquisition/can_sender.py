import can
import logging
import threading


class CANSender:
    """
    Handles CAN transmission via socketcan.
    Supports standard (11-bit) and extended (29-bit) IDs.
    """

    def __init__(self, interface="can0"):
        self.interface = interface
        self.bus = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger("CANSender")

    # =====================================================
    # CONNECT TO CAN BUS
    # =====================================================

    def connect(self):
        try:
            self.bus = can.interface.Bus(
                interface="socketcan",
                channel=self.interface
            )
            self.logger.info(f"CAN TX connected on {self.interface}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect CAN TX: {e}")
            self.bus = None
            return False

    # =====================================================
    # SEND CAN FRAME
    # =====================================================

    def send(self, arbitration_id, data, extended=False):
        """
        Send a CAN frame.

        Parameters:
        arbitration_id (int): CAN ID
        data (list[int] or bytes): payload (0-8 bytes)
        extended (bool): True for 29-bit ID
        """

        with self.lock:

            if self.bus is None:
                if not self.connect():
                    return False

            try:
                # Ensure payload is valid
                if isinstance(data, list):
                    payload = bytearray(data)
                elif isinstance(data, bytes):
                    payload = bytearray(data)
                else:
                    raise ValueError("Data must be list[int] or bytes")

                if len(payload) > 8:
                    raise ValueError("Classic CAN supports max 8 bytes")

                msg = can.Message(
                    arbitration_id=arbitration_id,
                    data=payload,
                    is_extended_id=extended
                )

                self.bus.send(msg)

                return True

            except can.CanError as e:
                self.logger.error(f"CAN send error: {e}")
                self._reset_bus()
                return False

            except Exception as e:
                self.logger.error(f"Invalid CAN TX request: {e}")
                return False

    # =====================================================
    # RESET BUS ON FAILURE
    # =====================================================

    def _reset_bus(self):
        try:
            if self.bus:
                self.bus.shutdown()
        except:
            pass

        self.bus = None

    # =====================================================
    # CLEANUP
    # =====================================================

    def shutdown(self):
        with self.lock:
            if self.bus:
                try:
                    self.bus.shutdown()
                    self.logger.info("CAN TX shutdown")
                except:
                    pass
                self.bus = None
