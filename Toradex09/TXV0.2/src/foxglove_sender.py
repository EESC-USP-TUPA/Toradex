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
        self.channels = {}
        self.logger = logging.getLogger("Foxglove")

    def start(self):
        self.loop = asyncio.new_event_loop()
        t = threading.Thread(
            target=self._run_server_thread,
            args=(self.loop,),
            daemon=True
        )
        t.start()
        self.logger.info(f"Servidor Foxglove iniciando na porta {self.port}")

    def _run_server_thread(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._async_main())

    async def _async_main(self):
        async with FoxgloveServer("0.0.0.0", self.port, "Embedded Telemetry") as server:
            self.server = server
            self.logger.info("Servidor Foxglove ONLINE")
            await asyncio.Future()

    def send_message(self, topic, payload):
        if self.server is None or self.loop is None:
            return

        asyncio.run_coroutine_threadsafe(
            self._ensure_channel_and_send(topic, payload),
            self.loop
        )

    async def _ensure_channel_and_send(self, topic, payload):
        try:
            if topic not in self.channels:
                channel_id = await self.server.add_channel(
                    {
                        "topic": topic,
                        "encoding": "json",
                        "schemaName": "Signal",
                        "schema": json.dumps({"type": "object"})
                    }
                )
                self.channels[topic] = channel_id

            await self.server.send_message(
                self.channels[topic],
                time.time_ns(),  # ⬅️ timestamp REAL (eixo X)
                json.dumps(payload).encode("utf-8")
            )
        except Exception as e:
            self.logger.error(f"Erro Foxglove: {e}")
