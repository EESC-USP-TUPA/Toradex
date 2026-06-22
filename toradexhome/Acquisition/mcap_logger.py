import time
import json
import sys
from pathlib import Path
from mcap.writer import Writer
import logging

class McapTelemetryLogger:
    def __init__(self, output_dir="/logs", max_file_size_mb=10, max_files=20):
        self.output_dir = Path(output_dir)
        # Cria a pasta caso não exista
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files
        
        self.current_file = None
        self.writer = None
        self.mcap_file_stream = None
        
        # Dicionários para armazenar schemas e canais dinamicamente
        self.schemas = {}
        self.channels = {}
        
        self._rotate_file()

    def _rotate_file(self):
        """Fecha o arquivo atual, rotaciona e abre um novo com buffer em RAM."""
        self.close()
        
        # Gerencia a rotação deletando os mais antigos
        files = sorted(self.output_dir.glob("telemetria_*.mcap"))
        while len(files) >= self.max_files:
            files[0].unlink()
            files = sorted(self.output_dir.glob("telemetria_*.mcap"))
            
        timestamp = int(time.time())
        filename = self.output_dir / f"telemetria_{timestamp}.mcap"
        
        # Abre o stream e inicia o Writer do MCAP com um chunk_size de 64KB (Buffer em RAM)
        self.mcap_file_stream = open(filename, "wb")
        self.writer = Writer(self.mcap_file_stream, chunk_size=1024 * 64)
        self.writer.start()
        
        self.current_file = filename
        # Ao criar um arquivo novo, precisamos resetar os canais
        self.schemas = {}
        self.channels = {}
        logging.info(f"Novo arquivo MCAP iniciado: {filename}")

    def _get_or_create_channel(self, source):
        """Registra o tópico no MCAP dinamicamente com base na chave 'source' do payload."""
        if source not in self.channels:
            # Registra um schema genérico de JSON
            schema_id = self.writer.register_schema(
                name=f"{source}_schema",
                encoding="jsonschema",
                data=b'{"type": "object"}'
            )
            self.schemas[source] = schema_id
            
            # Cria o tópico (ex: /veiculo/can, /veiculo/imu)
            channel_id = self.writer.register_channel(
                topic=f"/veiculo/{source}",
                message_encoding="json",
                schema_id=schema_id
            )
            self.channels[source] = channel_id
            
        return self.channels[source]

    def log_payload(self, payload):
        """Recebe o dicionário Python, converte para bytes e joga no buffer do MCAP."""
        if not self.writer:
            return

        # Pega o timestamp gerado pela aquisição ou cria um novo
        now_ns = payload.get("timestamp_ns", time.time_ns())
        source = payload.get("source", "unknown")

        channel_id = self._get_or_create_channel(source)

        # Transforma o dicionário em binário para salvar
        data_bytes = json.dumps(payload, separators=(",", ":")).encode('utf-8')

        # Grava na RAM (rápido, sem bloquear o sistema)
        self.writer.add_message(
            channel_id=channel_id,
            log_time=now_ns,
            publish_time=now_ns,
            sequence=0,
            data=data_bytes
        )

        # Checa se o arquivo atingiu os 10MB para rotacionar
        if self.current_file.stat().st_size >= self.max_file_size:
            self._rotate_file()

    def close(self):
        """Força o descarregamento da RAM para o disco (eMMC) e fecha os arquivos."""
        if self.writer:
            self.writer.finish()
            self.writer = None
        if self.mcap_file_stream:
            self.mcap_file_stream.close()
            self.mcap_file_stream = None