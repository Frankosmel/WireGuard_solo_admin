# storage.py

import os
import json

# Rutas de los archivos de almacenamiento
FILES = {
    "users": "data/users.json",       # Datos de clientes registrados (nombre, fecha, plan, etc.)
    "configs": "data/configs.json",   # Configuraciones WireGuard activas (clave pública, IP, etc.)
}

def ensure_storage():
    """
    Crea el directorio 'data/' y los archivos .json vacíos si no existen.
    """
    os.makedirs("data", exist_ok=True)
    for path in FILES.values():
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f, indent=4)

def load_json(name):
    """
    Carga un archivo JSON de los definidos en FILES.
    """
    path = FILES.get(name)
    if not path:
        raise ValueError(f"[❌] Archivo no reconocido: {name}")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(name, data):
    """
    Guarda un diccionario en el archivo JSON correspondiente.
    """
    path = FILES.get(name)
    if not path:
        raise ValueError(f"[❌] Archivo no reconocido: {name}")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# Funciones específicas para cada tipo de archivo

def load_users():
    """Carga los usuarios registrados"""
    return load_json("users")

def save_users(data):
    """Guarda los usuarios registrados"""
    save_json("users", data)

def load_configs():
    """Carga las configuraciones activas de WireGuard"""
    return load_json("configs")

def save_configs(data):
    """Guarda las configuraciones activas de WireGuard"""
    save_json("configs", data)

def get_next_available_ip():
    """
    Devuelve la próxima IP disponible para asignar a un nuevo cliente (evitando duplicados).
    Rango: 10.9.0.2 hasta 10.9.0.254
    """
    configs = load_configs()
    used_ips = {conf['ip'] for conf in configs.values()}
    for i in range(2, 255):
        ip = f"10.9.0.{i}"
        if ip not in used_ips:
            return ip
    return None  # Si no hay IPs disponibles
