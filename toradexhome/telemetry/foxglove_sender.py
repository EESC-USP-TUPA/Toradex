import json
import time
import asyncio
import threading
import logging
from foxglove_websocket.server import FoxgloveServer


class FoxgloveSender:
    def __init__(self, port=9000):
        self.port = port
        self.server = None
        self.loop = None
        self.channels = {}
        self.logger = logging.getLogger("FoxgloveSender")

    # ======================================================
    # START SERVER
    # ======================================================

    def start(self):
        self.loop = asyncio.new_event_loop()

        thread = threading.Thread(
            target=self._run_server,
            daemon=True
        )
        thread.start()

        self.logger.info(f"Foxglove server starting on port {self.port}")

    def _run_server(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_main())

    async def _async_main(self):
        async with FoxgloveServer(
            "0.0.0.0",
            self.port,
            "Vehicle Telemetry"
        ) as server:
            self.server = server
            self.logger.info("Foxglove ONLINE")
            await asyncio.Future()

    # ======================================================
    # SEND MESSAGE
    # ======================================================

    def send_message(self, topic, payload):

        if self.server is None or self.loop is None:
            return

        timestamp_ns = payload.get("timestamp_ns", time.time_ns())

        asyncio.run_coroutine_threadsafe(
            self._ensure_channel_and_send(topic, payload, timestamp_ns),
            self.loop
        )

    async def _ensure_channel_and_send(self, topic, payload, timestamp_ns):

        try:

            if topic not in self.channels:

                # -------------------------------
                # GPS Schema
                # -------------------------------
                if "latitude" in payload and "longitude" in payload:
                    schema = {
                        "type": "object",
                        "properties": {
                            "latitude": {"type": "number"},
                            "longitude": {"type": "number"},
                            "altitude": {"type": "number"},
                            "speed": {"type": "number"},
                            "heading": {"type": "number"},
                            "satellites": {"type": "number"},
                            "fix": {"type": "number"},
                            "timestamp_ns": {"type": "number"}
                        },
                        "required": ["latitude", "longitude"]
                    }

                # -------------------------------
                # Generic numeric schema (IMU, CAN)
                # -------------------------------
                else:
                    schema = {
                        "type": "object",
                        "properties": {
                            "value": {"type": "number"},
                            "unit": {"type": "string"},
                            "timestamp_ns": {"type": "number"}
                        },
                        "required": ["value"]
                    }

                # ✅ UNIQUE schema name per topic
                channel_id = await self.server.add_channel(
                    {
                        "topic": topic,
                        "encoding": "json",
                        "schemaName": f"{topic}_schema",
                        "schema": json.dumps(schema)
                    }
                )

                self.channels[topic] = channel_id
                self.logger.info(f"Channel created: {topic}")

            await self.server.send_message(
                self.channels[topic],
                timestamp_ns,
                json.dumps(payload).encode("utf-8")
            )

        except Exception as e:
            self.logger.error(f"Foxglove error ({topic}): {e}")
