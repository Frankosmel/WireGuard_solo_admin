# main.py

from telebot import TeleBot
from config import TOKEN, ADMIN_ID
from admin_handlers import register_admin_handlers
from utils import schedule_expiration_check
from storage import ensure_storage

# Inicializar el bot con el token y modo HTML
bot = TeleBot(TOKEN, parse_mode='HTML')

# Asegurar que los archivos de almacenamiento existan
ensure_storage()

# Registrar los comandos del administrador
register_admin_handlers(bot)

# Programar revisiones automáticas de vencimientos
schedule_expiration_check(bot)

print("✅ Bot de WireGuard iniciado correctamente.")

# Iniciar el bot en modo polling continuo
bot.infinity_polling()
