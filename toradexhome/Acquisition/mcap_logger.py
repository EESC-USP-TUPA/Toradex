import time
import json
from pathlib import Path
from mcap.writer import Writer
import logging
import threading  # <-- ADICIONADO para resolver a condição de corrida

class McapTelemetryLogger:
    def __init__(self, output_dir="/logs", max_file_size_mb=10, max_files=20):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files
        
        self.current_file = None
        self.writer = None
        self.mcap_file_stream = None
        
        self.schemas = {}
        self.channels = {}
        
        # Trava para garantir exclusão mútua entre IMU, GPS e CAN
        self.lock = threading.Lock()  # <-- ADICIONADO
        
        self._rotate_file()

    def _rotate_file(self):
        """Fecha o arquivo atual, rotaciona e abre um novo. (Chamado internamente com lock)"""
        self.close_internal()
        
        files = sorted(self.output_dir.glob("telemetria_*.mcap"))
        while len(files) >= self.max_files:
            files[0].unlink()
            files = sorted(self.output_dir.glob("telemetria_*.mcap"))
            
        timestamp = int(time.time())
        filename = self.output_dir / f"telemetria_{timestamp}.mcap"
        
        self.mcap_file_stream = open(filename, "wb")
        self.writer = Writer(self.mcap_file_stream, chunk_size=1024 * 64)
        self.writer.start()
        
        self.current_file = filename
        self.schemas = {}
        self.channels = {}
        logging.info(f"Novo arquivo MCAP iniciado: {filename}")

    def _get_or_create_channel(self, source):
        """Registra canais. Sempre executado dentro do bloco de lock."""
        if source not in self.channels:
            schema_id = self.writer.register_schema(
                name=f"{source}_schema",
                encoding="jsonschema",
                data=b'{"type": "object"}'
            )
            self.schemas[source] = schema_id
            
            channel_id = self.writer.register_channel(
                topic=f"/veiculo/{source}",
                message_encoding="json",
                schema_id=schema_id
            )
            self.channels[source] = channel_id
            
        return self.channels[source]

    def log_payload(self, payload):
        """Recebe o payload de forma thread-safe."""
        # Adquire a trava. Se outra thread estiver escrevendo, esta aguarda sua vez
        with self.lock:  
            if not self.writer:
                return

            try:
                now_ns = payload.get("timestamp_ns", time.time_ns())
                source = payload.get("source", "unknown")

                channel_id = self._get_or_create_channel(source)
                data_bytes = json.dumps(payload, separators=(",", ":")).encode('utf-8')

                self.writer.add_message(
                    channel_id=channel_id,
                    log_time=now_ns,
                    publish_time=now_ns,
                    sequence=0,
                    data=data_bytes
                )

                if self.current_file.stat().st_size >= self.max_file_size:
                    self._rotate_file()
            except Exception as e:
                # Evita que uma falha no log quebre o broadcast da rede
                logging.error(f"Erro interno no McapLogger: {e}")

    def close_internal(self):
        """Fecha os streams sem travar (uso interno)."""
        if self.writer:
            try:
                self.writer.finish()
            except:
                pass
            self.writer = None
        if self.mcap_file_stream:
            try:
                self.mcap_file_stream.close()
            except:
                pass
            self.mcap_file_stream = None

    def close(self):
        """Fecha o logger externamente de forma segura."""
        with self.lock:
            self.close_internal()