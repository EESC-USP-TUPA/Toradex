import json
import time
import asyncio
import threading
import logging
from foxglove_websocket.server import FoxgloveServer


class FoxgloveSender:
    def __init__(self, port=8765):
        self.port = port
        self.server = None
        self.loop = None
        self.channels = {}  # topic -> channel_id
        self.logger = logging.getLogger("FoxgloveSender")

    # =====================================================
    # START SERVER (NON-BLOCKING)
    # =====================================================

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
            "Telemetry Server"
        ) as server:
            self.server = server
            self.logger.info("Foxglove ONLINE")
            await asyncio.Future()  # keep alive

    # =====================================================
    # PUBLIC SEND METHOD
    # =====================================================

    def send_message(self, topic, payload):
        if self.server is None or self.loop is None:
            return

        timestamp_ns = payload.get("timestamp_ns", time.time_ns())

        asyncio.run_coroutine_threadsafe(
            self._ensure_channel_and_send(topic, payload, timestamp_ns),
            self.loop
        )

    # =====================================================
    # INTERNAL SEND
    # =====================================================

    async def _ensure_channel_and_send(self, topic, payload, timestamp_ns):
        try:
            # Create channel if not exists
            if topic not in self.channels:
                channel_id = await self.server.add_channel(
                    {
                        "topic": topic,
                        "encoding": "json",
                        "schemaName": "Signal",
                        "schema": json.dumps({
                            "type": "object",
                            "properties": {
                                "value": {"type": "number"},
                                "unit": {"type": "string"},
                                "timestamp_ns": {"type": "number"}
                            },
                            "required": ["value"]
                        })
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
            self.logger.error(f"Foxglove error on {topic}: {e}")
