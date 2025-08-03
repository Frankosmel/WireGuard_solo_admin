# admin_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMINS, PLANS
from storage import load_users, save_users
from utils import generate_keypair, get_next_available_ip, generate_conf, generate_qr_code, delete_conf
from datetime import datetime, timedelta

# Diccionario temporal para el flujo de creación
ADMIN_FLOW = {}

def is_admin(user_id):
    return user_id in ADMINS

def register_admin_handlers(bot: TeleBot):

    @bot.message_handler(commands=['admin'])
    def handle_admin(message):
        if not is_admin(message.from_user.id):
            return bot.reply_to(message, "⛔️ No tienes permisos para acceder a este panel.")
        show_admin_menu(bot, message.chat.id)

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📦 Crear configuración")
    def start_create_config(message):
        bot.send_message(message.chat.id, "🧾 Escribe un *nombre único* para el cliente (sin espacios ni símbolos):", parse_mode="Markdown")
        ADMIN_FLOW[message.from_user.id] = {'step': 'awaiting_name'}

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in ADMIN_FLOW and ADMIN_FLOW[m.from_user.id]['step'] == 'awaiting_name')
    def ask_plan(message):
        client_name = message.text.strip()
        if " " in client_name or not client_name.isalnum():
            return bot.reply_to(message, "⚠️ Nombre inválido. Usa solo letras y números, sin espacios.")
        
        ADMIN_FLOW[message.from_user.id]['client_name'] = client_name

        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for plan in PLANS.keys():
            kb.add(KeyboardButton(plan))
        bot.send_message(message.chat.id, "🕐 Selecciona un *plan de vencimiento*:", reply_markup=kb, parse_mode="Markdown")
        ADMIN_FLOW[message.from_user.id]['step'] = 'awaiting_plan'

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in ADMIN_FLOW and ADMIN_FLOW[m.from_user.id]['step'] == 'awaiting_plan')
    def generate_configuration(message):
        plan = message.text.strip()
        if plan not in PLANS:
            return bot.reply_to(message, "❌ Plan inválido. Selecciona una opción del teclado.")
        
        data = ADMIN_FLOW.pop(message.from_user.id)
        client_name = data['client_name']

        private_key, public_key = generate_keypair()
        ip = get_next_available_ip()
        if not ip:
            return bot.send_message(message.chat.id, "❌ No hay IPs disponibles.")
        
        path = generate_conf(client_name, private_key, ip, config.SERVER_PUBLIC_KEY)
        qr_image = generate_qr_code(path)

        vencimiento = datetime.utcnow() + timedelta(days=PLANS[plan])
        users = load_users()
        users[client_name] = {
            "ip": ip,
            "public_key": public_key,
            "vencimiento": vencimiento.isoformat(),
            "plan": plan
        }
        save_users(users)

        bot.send_message(message.chat.id, f"✅ Configuración generada para: *{client_name}*\n📅 Vence el: *{vencimiento.strftime('%Y-%m-%d %H:%M')} UTC*", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f)
        bot.send_photo(message.chat.id, qr_image, caption="📲 Escanea este código QR para importar la configuración en tu app.")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🗑 Eliminar configuración")
    def delete_config_prompt(message):
        users = load_users()
        if not users:
            return bot.send_message(message.chat.id, "ℹ️ No hay configuraciones activas.")

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for name in users:
            kb.add(KeyboardButton(name))
        bot.send_message(message.chat.id, "❌ Selecciona la configuración a eliminar:", reply_markup=kb)

        ADMIN_FLOW[message.from_user.id] = {'step': 'awaiting_delete'}

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in ADMIN_FLOW and ADMIN_FLOW[m.from_user.id]['step'] == 'awaiting_delete')
    def delete_config(message):
        client_name = message.text.strip()
        users = load_users()
        if client_name not in users:
            return bot.reply_to(message, "⚠️ Ese cliente no existe.")
        
        delete_conf(client_name)
        del users[client_name]
        save_users(users)

        bot.send_message(message.chat.id, f"✅ Configuración '{client_name}' eliminada correctamente.", reply_markup=ReplyKeyboardRemove())
        ADMIN_FLOW.pop(message.from_user.id)

def show_admin_menu(bot: TeleBot, chat_id: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📦 Crear configuración"))
    kb.add(KeyboardButton("🗑 Eliminar configuración"))
    bot.send_message(chat_id, "🔧 *Panel de Administrador*", reply_markup=kb, parse_mode="Markdown")
