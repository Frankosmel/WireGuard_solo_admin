# utils.py

import os
import json
import subprocess
import qrcode
from config import WG_CONFIG_DIR, SERVER_PUBLIC_KEY, SERVER_ENDPOINT, WG_PORT, WG_NETWORK_RANGE
from storage import load_users, save_users
from datetime import datetime
from threading import Timer

def get_used_ips():
    """
    Obtiene las IPs ya asignadas a clientes existentes.
    """
    users = load_users()
    return {data['ip'] for data in users.values()}

def get_next_ip():
    """
    Busca la próxima IP libre dentro del rango 10.9.0.2 - 10.9.0.254.
    """
    used_ips = get_used_ips()
    base_ip = "10.9.0."
    for i in range(2, 255):
        candidate = f"{base_ip}{i}"
        if candidate not in used_ips:
            return candidate
    raise RuntimeError("🚫 No hay IPs disponibles.")

def generate_keys():
    """
    Genera un par de claves privadas/públicas con wg.
    """
    private_key = subprocess.check_output("wg genkey", shell=True).decode().strip()
    public_key = subprocess.check_output(f"echo {private_key} | wg pubkey", shell=True).decode().strip()
    return private_key, public_key

def generate_wg_config(client_name: str, vencimiento: str) -> dict:
    """
    Genera el archivo de configuración .conf y devuelve info completa del cliente.
    """
    try:
        ip = get_next_ip()
        private_key, public_key = generate_keys()

        config_text = f"""
[Interface]
PrivateKey = {private_key}
Address = {ip}/32
DNS = 1.1.1.1

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_ENDPOINT}:{WG_PORT}
AllowedIPs = {WG_NETWORK_RANGE}
PersistentKeepalive = 25
""".strip()

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
        raise RuntimeError(f"No se pudo generar la configuración: {str(e)}")

def generate_qr_code(conf_path: str):
    """
    Genera un código QR a partir del archivo .conf existente.
    """
    with open(conf_path, "r") as f:
        config_text = f.read()

    qr = qrcode.make(config_text)
    qr_path = conf_path.replace(".conf", "_qr.png")
    qr.save(qr_path)
    return qr_path

def delete_conf(client_name: str):
    """
    Elimina el archivo .conf asociado a un cliente.
    """
    path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
    qr_path = os.path.join(WG_CONFIG_DIR, f"{client_name}_qr.png")

    if os.path.exists(path):
        os.remove(path)
    if os.path.exists(qr_path):
        os.remove(qr_path)

def schedule_expiration_check(bot):
    """
    Verifica cada 60 minutos si alguna configuración venció y la elimina.
    """
    def check_expired():
        users = load_users()
        now = datetime.utcnow()
        updated = {}

        for name, data in users.items():
            vencimiento = datetime.strptime(data["vencimiento"], "%Y-%m-%d %H:%M:%S")
            if vencimiento > now:
                updated[name] = data
            else:
                delete_conf(name)
                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"⏰ Configuración vencida y eliminada: <b>{name}</b>\n🧾 IP: {data['ip']}",
                        parse_mode="HTML"
                    )
                except:
                    pass

        save_users(updated)
        Timer(3600, check_expired).start()  # Revisa cada 60 minutos

    check_expired()
