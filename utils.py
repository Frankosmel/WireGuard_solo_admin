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


def generate_keypair():
    """
    Genera un par de claves WireGuard (privada y pública).
    """
    try:
        private_key = subprocess.check_output(['wg', 'genkey']).decode().strip()
        public_key = subprocess.run(
            ['wg', 'pubkey'],
            input=private_key.encode(),
            capture_output=True,
            check=True
        ).stdout.decode().strip()

        if len(private_key) != 44 or len(public_key) != 44:
            raise ValueError("❌ Las claves deben tener exactamente 44 caracteres base64.")

        return private_key, public_key
    except Exception as e:
        print(f"❌ Error al generar las claves: {e}")
        raise


def get_used_ips():
    """
    Devuelve el conjunto de IPs ya asignadas en el archivo users.json.
    """
    used_ips = set()
    users = load_json("users")
    for data in users.values():
        ip = data.get("ip")
        if ip:
            used_ips.add(ip)
    return used_ips


def get_active_wg_ips():
    """
    Devuelve el conjunto de IPs activas actualmente en wg0.
    """
    try:
        output = subprocess.check_output(['wg', 'show', 'wg0', 'allowed-ips']).decode()
        return set(line.split()[0] for line in output.splitlines())
    except Exception:
        return set()


def get_next_available_ip():
    """
    Encuentra la próxima IP disponible en el rango 10.9.0.2 - 10.9.0.254.
    """
    base = ipaddress.IPv4Address("10.9.0.1")
    used_ips = get_used_ips()
    active_ips = get_active_wg_ips()
    all_used = used_ips.union(active_ips)

    for i in range(2, 255):
        candidate = str(base + i)
        if candidate not in all_used:
            return candidate
    return None


def peer_already_exists(public_key):
    """
    Verifica si una clave pública ya está agregada como peer en wg0.
    """
    try:
        output = subprocess.check_output(['wg', 'show', 'wg0', 'dump']).decode()
        return public_key in output
    except Exception:
        return False


def generate_conf(client_name, private_key, ip):
    """
    Genera el archivo de configuración .conf de WireGuard para el cliente.
    """
    config = f"""[Interface]
PrivateKey = {private_key}
Address = {ip}/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_PUBLIC_IP}:{LISTEN_PORT}
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
"""
    try:
        os.makedirs(WG_CONFIG_DIR, exist_ok=True)
        path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
        with open(path, "w") as f:
            f.write(config)
        return path
    except Exception as e:
        print(f"❌ Error al generar el archivo .conf: {e}")
        raise


def generate_qr_code(config_path):
    """
    Genera un código QR a partir del archivo de configuración .conf.
    """
    try:
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
    except Exception as e:
        print(f"❌ Error al generar el código QR: {e}")
        raise


def delete_conf(client_name):
    """
    Elimina el archivo de configuración .conf de un cliente.
    """
    path = os.path.join(WG_CONFIG_DIR, f"{client_name}.conf")
    if os.path.exists(path):
        os.remove(path)
        return True
    return False


def schedule_expiration_check(bot):
    """
    Hilo que revisa periódicamente el vencimiento de las configuraciones.
    """
    def check_loop():
        while True:
            try:
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
                            except Exception as e:
                                print(f"⚠️ Error al notificar vencimiento: {e}")
                            data[f"avisado_{aviso}"] = True

                    if horas_restantes <= 0 and not data.get("expirado", False):
                        delete_conf(client_name)
                        try:
                            bot.send_message(
                                int(ADMIN_ID),
                                f"📛 Expiró la configuración de `{client_name}`.",
                                parse_mode="Markdown"
                            )
                        except Exception as e:
                            print(f"⚠️ Error al notificar expiración: {e}")
                        data["expirado"] = True

                save_json("users", users)
                sleep(REVISIÓN_INTERVALO_SEGUNDOS)
            except Exception as e:
                print(f"❌ Error inesperado en revisión de expiraciones: {e}")
                sleep(30)

    Thread(target=check_loop, daemon=True).start()


def enable_ip_forwarding():
    """
    Habilita el reenvío de IP y configura iptables para permitir acceso a Internet desde clientes WireGuard.
    """
    try:
        # Activar el reenvío temporalmente
        subprocess.run(["sysctl", "-w", "net.ipv4.ip_forward=1"], check=True)

        # Hacerlo permanente (si aún no lo es)
        with open("/etc/sysctl.conf", "a") as sysctl_conf:
            sysctl_conf.write("\nnet.ipv4.ip_forward=1\n")
        subprocess.run(["sysctl", "-p"], check=True)

        # Reglas de NAT con iptables si aún no existen
        result = subprocess.run(
            ["iptables", "-t", "nat", "-C", "POSTROUTING", "-o", "enX0", "-j", "MASQUERADE"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        if result.returncode != 0:
            subprocess.run(["iptables", "-t", "nat", "-A", "POSTROUTING", "-o", "enX0", "-j", "MASQUERADE"], check=True)

        # Permitir tráfico entrante y saliente a través de wg0
        subprocess.run(["iptables", "-A", "FORWARD", "-i", "wg0", "-j", "ACCEPT"], check=True)
        subprocess.run(["iptables", "-A", "FORWARD", "-o", "wg0", "-j", "ACCEPT"], check=True)

        print("✅ Reenvío de IP y reglas NAT configuradas correctamente.")
    except Exception as e:
        print(f"❌ Error al configurar el reenvío de IP: {e}")


def generate_wg_config(name, expiration_date, *args):
    """
    Genera configuración, claves, IP, agrega el peer, guarda en users y retorna el QR.
    """
    users = load_json("users")

    if name in users:
        raise ValueError("⚠️ Este nombre ya está registrado.")

    ip = get_next_available_ip()
    if not ip:
        raise RuntimeError("❌ No hay IPs disponibles en el rango asignado.")

    private_key, public_key = generate_keypair()

    if peer_already_exists(public_key):
        raise RuntimeError("🚫 Ya existe un peer con esta clave pública en el servidor.")

    config_path = generate_conf(name, private_key, ip)

    try:
        subprocess.run(
            ["sudo", "wg", "set", "wg0", "peer", public_key, "allowed-ips", f"{ip}/32"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al agregar peer al servidor: {e}")
        raise RuntimeError(f"❌ Error al agregar el peer al servidor: {e}")

    users[name] = {
        "nombre": name,
        "ip": ip,
        "public_key": public_key,
        "private_key": private_key,
        "vencimiento": expiration_date,
        "expirado": False
    }

    save_json("users", users)
    qr_image = generate_qr_code(config_path)

    return {
        "nombre": name,
        "ip": ip,
        "public_key": public_key,
        "private_key": private_key,
        "conf_path": config_path,
        "qr": qr_image
    }


# Ejecutar al cargar el archivo para asegurar la configuración de red
enable_ip_forwarding()
