# storage.py

import os
import json

# Definición de rutas de archivos de almacenamiento
FILES = {
    "users": "data/users.json",       # Datos de clientes registrados
    "configs": "data/configs.json",   # Configuraciones WireGuard activas
}

def ensure_storage():
    """
    Asegura que el directorio 'data/' y los archivos JSON existan.
    Si no existen, los crea vacíos como diccionarios.
    """
    os.makedirs("data", exist_ok=True)
    for path in FILES.values():
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f, indent=4)

def load_json(name):
    """
    Carga un archivo JSON según su clave lógica en FILES.
    Retorna un diccionario con los datos.
    """
    path = FILES.get(name)
    if not path:
        raise ValueError(f"Archivo desconocido: {name}")
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_json(name, data):
    """
    Guarda un diccionario en el archivo JSON correspondiente a la clave.
    """
    path = FILES.get(name)
    if not path:
        raise ValueError(f"Archivo desconocido: {name}")
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

# Alias específicos usados por otros módulos
def load_users():
    return load_json("users")

def save_users(data):
    save_json("users", data)

def load_configs():
    return load_json("configs")

def save_configs(data):
    save_json("configs", data)
