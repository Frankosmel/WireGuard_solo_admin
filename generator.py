# generator.py

import os, subprocess
from config import SERVER_PUBLIC_KEY, SERVER_PUBLIC_IP, LISTEN_PORT
from utils import get_next_ip, guardar_archivo

def generar_configuracion(nombre_cliente: str):
    try:
        private_key = subprocess.check_output(["wg", "genkey"]).decode().strip()
        public_key = subprocess.check_output(["bash", "-c", f"echo {private_key} | wg pubkey"]).decode().strip()
        ip_cliente = get_next_ip()

        config_text = f"""[Interface]
PrivateKey = {private_key}
Address = {ip_cliente}/32
DNS = 1.1.1.1

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_PUBLIC_IP}:{LISTEN_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""

        # Nombre del archivo .conf
        nombre_archivo = f"{nombre_cliente}_{ip_cliente.replace('/', '')}.conf"
        ruta = os.path.join("/etc/wireguard/configs", nombre_archivo)
        guardar_archivo(ruta, config_text)

        return {
            "status": "ok",
            "private_key": private_key,
            "public_key": public_key,
            "ip": ip_cliente,
            "conf_path": ruta
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
