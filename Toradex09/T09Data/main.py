import os
import time
import shutil
import sys

# Configurações
DATA_DIR = "/datalogger"
USB_MOUNT_POINT = "/var/rootdirs/media/EE8D-F793"
CHECK_INTERVAL = 10  # segundos

def log(message):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    sys.stdout.flush()

def is_usb_connected():
    return os.path.exists(USB_MOUNT_POINT)

def copy_data():
    try:
        if not os.path.exists(DATA_DIR):
            log("AVISO: Diretório de dados não encontrado")
            return False
        
        if not os.listdir(DATA_DIR):
            log("AVISO: Nenhum dado para copiar")
            return True
            
        shutil.copytree(DATA_DIR, USB_MOUNT_POINT, dirs_exist_ok=True)
        log(" Transferência finalizada")
        return True
    except Exception as e:
        log(f"Erro na cópia: {e}")
        return False

def main():
    log("Serviço de transferência USB iniciado")
    
    retry_count = 0
    max_retries = 3
    
    while True:
        if is_usb_connected():
            log("Pendrive conectado")
            
            if copy_data():
                retry_count = 0  # Reset do contador em caso de sucesso
                time.sleep(30)   # Espera 30s após transferência bem-sucedida
            else:
                retry_count += 1
                if retry_count >= max_retries:
                    log("Desistindo da conexão atual")
                    retry_count = 0
                    time.sleep(30)
                else:
                    log(f"Tentando novamente ({retry_count}/{max_retries})")
                    time.sleep(5)
        else:
            log("Pendrive não conectado")
            retry_count = 0
            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
