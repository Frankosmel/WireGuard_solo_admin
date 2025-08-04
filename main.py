# main.py

from telebot import TeleBot
from config import TOKEN
from admin_handlers import register_admin_handlers
from utils import schedule_expiration_check
from storage import ensure_storage

# Inicializar el bot con el token y modo HTML
bot = TeleBot(TOKEN, parse_mode='HTML')

# Asegurar que existan los archivos necesarios
ensure_storage()

# Registrar comandos y flujos del panel de administración
register_admin_handlers(bot)

# Programar verificación automática de vencimientos
schedule_expiration_check(bot)

print("✅ Bot de WireGuard iniciado correctamente.")

# Iniciar el bot en modo polling continuo
bot.infinity_polling()
