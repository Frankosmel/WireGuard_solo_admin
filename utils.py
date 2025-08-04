# utils.py

import subprocess
import os
import ipaddress
import qrcode
from io import BytesIO
from threading import Thread
from time import sleep
from datetime import datetime

from config import (
    WG_CONFIG_DIR,
    SERVER_PUBLIC_IP,
    LISTEN_PORT,
    AVISOS_VENCIMIENTO_HORAS,
    REVISIÓN_INTERVALO_SEGUNDOS,
    ADMIN_ID,
    SERVER_PUBLIC_KEY
)

from storage import load_json, save_json

# 🔐 Genera par de claves (privada y pública)
def generate_keypair():
    private_key = subprocess.check_output("wg genkey", shell=True).decode().strip()
    public_key = subprocess.check_output(f"echo {private_key} | wg pubkey", shell=True).decode().strip()
    return private_key, public_key

# 📋 Obtiene IPs ya asignadas
def get_used_ips():
    used_ips = set()
    users = load_json("users")
    for data in users.values():
        ip = data.get("ip")
        if ip:
            used_ips.add(ip)
    return used_ips

# 🔢 Encuentra la próxima IP disponible en el rango 10.9.0.2 - 10.9.0.254
def get_next_available_ip():
    base = ipaddress.IPv4Address("10.9.0.1")
    used_ips = get_used_ips()
    for i in range(2, 255):
        candidate = str(base + i)
        if candidate not in used_ips:
            return candidate
    return None

# 📝 Genera archivo .conf de cliente
def generate_conf(client_name, private_key, ip):
    config = f"""[Interface]
PrivateKey = {private_key}
Address = {ip}/32
DNS = 1.1.1.1

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_PUBLIC_IP}:{LISTEN_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    os.makedirs(WG_CONFIG_DIR, exist_ok=True)
    path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
    with open(path, "w") as f:
        f.write(config)
    return path

# 📲 Genera código QR desde .conf
def generate_qr_code(config_path):
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

# 🗑 Elimina archivo de configuración
def delete_conf(client_name):
    path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False

# ⏳ Verifica vencimientos y notifica automáticamente
def schedule_expiration_check(bot):
    def check_loop():
        while True:
            users = load_json("users")
            now = datetime.now()

            for client_name, data in users.items():
                venc = data.get("vencimiento")
                if not venc:
                    continue

                try:
                    vencimiento = datetime.strptime(venc, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    try:
                        vencimiento = datetime.strptime(venc, "%Y-%m-%d")
                    except ValueError:
                        continue

                horas_restantes = (vencimiento - now).total_seconds() / 3600

                for aviso in AVISOS_VENCIMIENTO_HORAS:
                    if int(horas_restantes) == aviso and not data.get(f"avisado_{aviso}", False):
                        try:
                            bot.send_message(
                                int(ADMIN_ID),
                                f"🔔 Aviso: La configuración `{client_name}` vence en *{aviso} horas*.",
                                parse_mode="Markdown"
                            )
                        except:
                            pass
                        data[f"avisado_{aviso}"] = True

                if horas_restantes <= 0 and not data.get("expirado", False):
                    delete_conf(client_name)
                    try:
                        bot.send_message(int(ADMIN_ID), f"📛 Expiró la configuración de `{client_name}`.", parse_mode="Markdown")
                    except:
                        pass
                    data["expirado"] = True

            save_json("users", users)
            sleep(REVISIÓN_INTERVALO_SEGUNDOS)

    Thread(target=check_loop, daemon=True).start()

# 🔧 Genera la configuración completa del cliente
def generate_wg_config(name, expiration_date):
    users = load_json("users")

    if name in users:
        raise ValueError("Este nombre ya está registrado.")

    ip = get_next_available_ip()
    if not ip:
        raise RuntimeError("No hay IPs disponibles en el rango asignado.")

    private_key, public_key = generate_keypair()
    config_path = generate_conf(name, private_key, ip)

    # ✅ Verifica si el peer ya existe antes de intentar agregarlo
    result = subprocess.run(["wg", "show", "wg0", "peers"], capture_output=True, text=True)
    if public_key not in result.stdout:
        try:
            subprocess.run(
                ["wg", "set", "wg0", "peer", public_key, "allowed-ips", f"{ip}/32"],
                check=True
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"❌ Error al agregar el peer al servidor: {e}")

    users[name] = {
        "nombre": name,
        "ip": ip,
        "clave_publica": public_key,
        "vencimiento": expiration_date,
        "expirado": False
    }

    save_json("users", users)

    qr_image = generate_qr_code(config_path)

    return {
        "nombre": name,
        "ip": ip,
        "clave_publica": public_key,
        "conf_path": config_path,
        "qr": qr_image
                      }
