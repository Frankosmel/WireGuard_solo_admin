# storage.py

import os
import json

# Definiciones de archivos de almacenamiento
FILES = {
    "users": "data/users.json",
    "configs": "data/configs.json",
}

def ensure_storage():
    """
    Crea los archivos y directorio `data/` si no existen.
    Inicializa cada archivo como un diccionario vacío si está ausente.
    """
    os.makedirs("data", exist_ok=True)
    for path in FILES.values():
        if not os.path.exists(path):
            with open(path, "w") as f:
                json.dump({}, f, indent=4)

def load_json(name):
    """
    Carga un archivo JSON por su nombre lógico (clave de FILES).
    """
    path = FILES.get(name)
    if not path:
        raise ValueError(f"Archivo desconocido: {name}")
    with open(path, "r") as f:
        return json.load(f)

def save_json(name, data):
    """
    Guarda un diccionario en el archivo JSON correspondiente.
    """
    path
