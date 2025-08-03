h# config.py

# Token del bot (reemplaza con tu token real)
TOKEN = "TU_TOKEN_AQUI"

# ID del administrador autorizado
ADMIN_ID = 1383931339  # Cambia este ID si es necesario

# Dirección IP pública del servidor con WireGuard
SERVER_PUBLIC_IP = "123.123.123.123"  # Reemplaza con la IP real

# Puerto de escucha de WireGuard
LISTEN_PORT = 51820

# Carpeta donde se guardarán los archivos .conf
WG_CONFIG_DIR = "configs"

# Archivo JSON con la información de los clientes
CLIENTES_FILE = "clientes.json"

# Intervalo de revisión de vencimientos en segundos
REVISIÓN_INTERVALO_SEGUNDOS = 3600  # cada 1 hora

# Horas antes del vencimiento para enviar notificaciones
AVISOS_VENCIMIENTO_HORAS = [72, 24, 0]  # 3 días, 1 día, el mismo día

# Nombres visibles de los planes (no se muestran precios al usuario)
PLANES = [
    "Free (5 horas)",
    "15 días",
    "30 días"
]

# Precios internos por método de pago (no mostrados al usuario)
PLANES_PRECIOS = {
    "Free (5 horas)": {"horas": 5, "precio_cup": 0, "precio_saldo": 0},
    "15 días": {"dias": 15, "precio_cup": 500, "precio_saldo": 250},
    "30 días": {"dias": 30, "precio_cup": 750, "precio_saldo": 375}
}

# Métodos de pago disponibles (seleccionables por botón)
METODOS_PAGO = ["CUP", "Saldo Móvil"]

# Grupo o canal de log (opcional, dejar en None si no se usa)
GRUPO_LOGS = None
