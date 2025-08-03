# main.py

from telebot import TeleBot
from config import TOKEN, ADMIN_ID
from client_handlers import register_client_handlers
from admin_handlers import register_admin_handlers
from utils import schedule_expiration_check
from storage import ensure_storage

bot = TeleBot(TOKEN, parse_mode='HTML')

# Asegurar que existan los archivos de almacenamiento
ensure_storage()

# Registrar handlers
register_client_handlers(bot)
register_admin_handlers(bot)

# Iniciar verificación programada de expiraciones
schedule_expiration_check(bot)

print("✅ Bot de WireGuard iniciado correctamente.")

bot.infinity_polling()
