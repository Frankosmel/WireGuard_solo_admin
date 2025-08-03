# utils.py

import subprocess
import os
import ipaddress
import qrcode
from io import BytesIO
from config import WG_CONFIG_DIR, SERVER_PUBLIC_IP, LISTEN_PORT
from storage import load_users

def generate_keypair():
    """
    Genera una clave privada y pública única para un nuevo cliente.
    """
    private_key = subprocess.check_output("wg genkey", shell=True).decode().strip()
    public_key = subprocess.check_output(f"echo {private_key} | wg pubkey", shell=True).decode().strip()
    return private_key, public_key

def get_used_ips():
    """
    Devuelve una lista de IPs ya asignadas a clientes.
    """
    used_ips = set()
    users = load_users()
    for user_id, data in users.items():
        ip = data.get("ip")
        if ip:
            used_ips.add(ip)
    return used_ips

def get_next_available_ip():
    """
    Calcula la próxima IP disponible dentro del rango 10.9.0.2 a 10.9.0.254.
    """
    base = ipaddress.IPv4Address("10.9.0.1")
    used_ips = get_used_ips()
    for i in range(2, 255):
        candidate = str(base + i)
        if candidate not in used_ips:
            return candidate
    return None

def generate_conf(client_name, private_key, ip, server_pubkey):
    """
    Genera el archivo de configuración .conf del cliente.
    """
    config = f"""[Interface]
PrivateKey = {private_key}
Address = {ip}/32
DNS = 1.1.1.1

[Peer]
PublicKey = {server_pubkey}
Endpoint = {SERVER_PUBLIC_IP}:{LISTEN_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
    with open(path, "w") as f:
        f.write(config)
    return path

def generate_qr_code(config_path):
    """
    Genera un código QR desde el contenido del archivo de configuración.
    """
    with open(config_path, "r") as f:
        content = f.read()
    qr = qrcode.QRCode(border=1)
    qr.add_data(content)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    bio = BytesIO()
    img.save(bio, format='PNG')
    bio.seek(0)
    return bio

def delete_conf(client_name):
    """
    Elimina el archivo de configuración del cliente.
    """
    path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False
