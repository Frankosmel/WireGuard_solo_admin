# utils.py

import os
import json
import subprocess
import qrcode
from datetime import datetime
from threading import Timer

from config import (
    WG_CONFIG_DIR,
    SERVER_PUBLIC_KEY,
    SERVER_ENDPOINT,
    WG_PORT,
    WG_NETWORK_RANGE,
    ADMIN_ID
)
from storage import load_users, save_users


def get_used_ips():
    """
    Obtiene las IPs ya asignadas actualmente a clientes registrados.
    """
    users = load_users()
    return {data['ip'] for data in users.values()}


def get_next_ip():
    """
    Busca la próxima IP disponible dentro del rango 10.9.0.2 - 10.9.0.254.
    """
    used_ips = get_used_ips()
    base_ip = "10.9.0."
    for i in range(2, 255):
        ip = f"{base_ip}{i}"
        if ip not in used_ips:
            return ip
    raise RuntimeError("🚫 No hay IPs disponibles. Todas las direcciones están en uso.")


def generate_keys():
    """
    Genera claves privada y pública para WireGuard.
    """
    try:
        private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
        public_key = subprocess.run(
            ['wg', 'pubkey'],
            input=private_key.encode(),
            capture_output=True,
            check=True
        ).stdout.decode().strip()

        if not private_key or not public_key:
            raise ValueError("Error al generar claves WireGuard.")
        return private_key, public_key

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"❌ Error generando claves: {e}")


def generate_wg_config(client_name: str, vencimiento: str) -> dict:
    """
    Genera el archivo .conf de un cliente y devuelve su info.
    """
    try:
        ip = get_next_ip()
        private_key, public_key = generate_keys()

        config_text = f"""[Interface]
PrivateKey = {private_key}
Address = {ip}/32
DNS = 1.1.1.1

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_ENDPOINT}:{WG_PORT}
AllowedIPs = {WG_NETWORK_RANGE}
PersistentKeepalive = 25
"""

        os.makedirs(WG_CONFIG_DIR, exist_ok=True)
        conf_path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")

        with open(conf_path, "w") as f:
            f.write(config_text)

        return {
            "ip": ip,
            "private_key": private_key,
            "public_key": public_key,
            "conf_path": conf_path
        }

    except Exception as e:
        raise RuntimeError(f"⚠️ No se pudo generar la configuración: {e}")


def generate_qr_code(conf_path: str):
    """
    Genera y guarda un QR desde un archivo .conf.
    """
    try:
        with open(conf_path, "r") as f:
            config_text = f.read()

        qr = qrcode.make(config_text)
        qr_path = conf_path.replace(".conf", "_qr.png")
        qr.save(qr_path)
        return qr_path
    except Exception as e:
        raise RuntimeError(f"❌ Error al generar el QR: {e}")


def delete_conf(client_name: str):
    """
    Elimina el archivo .conf y su QR.
    """
    conf_path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
    qr_path = conf_path.replace(".conf", "_qr.png")

    if os.path.exists(conf_path):
        os.remove(conf_path)
    if os.path.exists(qr_path):
        os.remove(qr_path)


def guardar_archivo(ruta: str, contenido: str):
    """
    Guarda texto en una ruta específica.
    """
    with open(ruta, "w") as f:
        f.write(contenido)


def schedule_expiration_check(bot):
    """
    Revisa cada 60 minutos si hay configuraciones vencidas.
    Si lo están, las elimina y notifica al administrador.
    """
    def check_expired():
        users = load_users()
        now = datetime.utcnow()
        activos = {}

        for nombre, datos in users.items():
            vencimiento = datetime.strptime(datos["vencimiento"], "%Y-%m-%d %H:%M:%S")
            if vencimiento > now:
                activos[nombre] = datos
            else:
                delete_conf(nombre)
                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"⛔️ Configuración vencida: <b>{nombre}</b>\n🧾 IP: {datos['ip']}",
                        parse_mode="HTML"
                    )
                except:
                    pass

        save_users(activos)
        Timer(3600, check_expired).start()  # Repetir cada 60 minutos

    check_expired()
