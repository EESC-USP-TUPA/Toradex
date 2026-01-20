import json
import time
import asyncio
import threading
import logging

# MUDANÇA 1: O import correto é do submódulo .server
from foxglove_websocket.server import FoxgloveServer

class FoxgloveSender:
    def __init__(self, port=8765):
        self.port = port
        self.server = None
        self.loop = None
        self.channels = {}  # Mapa de Tópico -> ID do Canal
        self.logger = logging.getLogger("Foxglove")

    def start(self):
        """Inicia o servidor em uma Thread separada"""
        # Cria um novo loop de eventos para a thread
        self.loop = asyncio.new_event_loop()
        
        # Roda a thread em modo 'daemon' para fechar quando o programa fechar
        t = threading.Thread(target=self._run_server_thread, args=(self.loop,), daemon=True)
        t.start()
        print(f"📡 Servidor Foxglove iniciando na porta {self.port}...")

    def _run_server_thread(self, loop):
        """Função interna que roda o loop asyncio"""
        asyncio.set_event_loop(loop)
        
        # Dispara a corrotina principal que segura o servidor de pé
        loop.run_until_complete(self._async_main())

    async def _async_main(self):
        """Mantém o servidor rodando dentro do Context Manager"""
        # MUDANÇA 2: Usa 'async with' para iniciar e gerenciar o servidor corretamente
        async with FoxgloveServer("0.0.0.0", self.port, "Toradex Verdin") as server:
            self.server = server
            print("✅ Servidor Foxglove ONLINE e aguardando conexões.")
            
            # Cria uma Future que nunca termina para manter o loop rodando
            await asyncio.Future()

    def send_message(self, message):
        """Recebe a mensagem CAN (síncrona) e envia para o WebSocket (assíncrono)"""
        if self.server is None or self.loop is None:
            return # Servidor ainda não está pronto

        # 1. Prepara os dados
        can_id_hex = f"0x{message.arbitration_id:X}"
        topic = f"/can/{can_id_hex}"
        
        payload = {
            "id": can_id_hex,
            "dlc": message.dlc,
            "data": list(message.data)
        }

        # 2. Agenda o envio na thread do asyncio
        # run_coroutine_threadsafe é thread-safe e não bloqueia o Main Loop da CAN
        asyncio.run_coroutine_threadsafe(
            self._ensure_channel_and_send(topic, payload), 
            self.loop
        )

    async def _ensure_channel_and_send(self, topic, payload):
        """Lógica assíncrona de envio"""
        try:
            # Se o canal ainda não existe, cria
            if topic not in self.channels:
                channel_id = await self.server.add_channel(
                    {
                        "topic": topic,
                        "encoding": "json",
                        "schemaName": "CanMsg",
                        "schema": json.dumps({"type": "object"})
                    }
                )
                self.channels[topic] = channel_id

            # Envia a mensagem
            await self.server.send_message(
                self.channels[topic],
                time.time_ns(),
                json.dumps(payload).encode('utf-8')
            )
        except Exception as e:
            print(f"Erro no envio Foxglove: {e}")