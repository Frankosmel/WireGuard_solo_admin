# config.py

# Token del bot (reemplázalo con tu token real)
TOKEN = "TU_TOKEN_AQUI"

# ID del administrador autorizado (solo este accede al bot)
ADMIN_ID = 1383931339  # Reemplaza por tu ID si cambia

# IP pública del servidor WireGuard (donde corre el bot y WG)
SERVER_PUBLIC_IP = "3.145.41.118"  # IP de tu VPS

# Clave pública del servidor WireGuard (para crear .conf)
SERVER_PUBLIC_KEY = "QLtoHUIcW2s/ZZ3tgKZ3wSidEy778prOGWIGo2cXhHw="

# Puerto de escucha del servidor WireGuard (por defecto 51820)
LISTEN_PORT = 51820

# Carpeta donde se almacenan los archivos .conf generados
WG_CONFIG_DIR = "/etc/wireguard/configs"

# Archivo JSON con las configuraciones de clientes registradas
CLIENTES_FILE = "clientes.json"

# Intervalo de revisión de vencimientos (en segundos)
REVISIÓN_INTERVALO_SEGUNDOS = 3600  # cada 1 hora

# Horas antes del vencimiento para enviar recordatorios automáticos
AVISOS_VENCIMIENTO_HORAS = [72, 24, 0]  # 3 días, 1 día, día final

# Planes disponibles (nombres mostrados en botones del bot)
PLANES = [
    "Free (5 horas)",
    "15 días",
    "30 días"
]

# Definición de duración y precio interno de cada plan
# (Los precios no se muestran en el bot ya que el administrador gestiona todo)
PLANES_PRECIOS = {
    "Free (5 horas)": {"horas": 5, "precio_cup": 0, "precio_saldo": 0},
    "15 días": {"dias": 15, "precio_cup": 500, "precio_saldo": 250},
    "30 días": {"dias": 30, "precio_cup": 750, "precio_saldo": 375}
}

# Métodos de pago disponibles (no usados ahora, pero listos para futuro)
METODOS_PAGO = ["CUP", "Saldo Móvil"]

# Rango de IPs permitido para los clientes (usado en utils.py)
WG_NETWORK_RANGE = "0.0.0.0/0"

# Dominio o IP + puerto para el endpoint que aparece en el .conf
SERVER_ENDPOINT = f"{SERVER_PUBLIC_IP}"

# Grupo o canal para recibir logs de actividad (puedes activarlo luego)
GRUPO_LOGS = None
