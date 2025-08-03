# admin_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMIN_ID, PLANES, PLANES_PRECIOS, SERVER_PUBLIC_IP
from storage import load_users, save_users
from utils import generate_keypair, get_next_available_ip, generate_conf, generate_qr_code, delete_conf
from datetime import datetime, timedelta
import os

# Diccionario temporal para controlar los pasos del flujo
ADMIN_FLOW = {}

# Verifica si el usuario es el administrador
def is_admin(user_id):
    return user_id == ADMIN_ID

# Registro de todos los handlers del administrador
def register_admin_handlers(bot: TeleBot):

    @bot.message_handler(commands=['admin'])
    def handle_admin_command(message):
        if not is_admin(message.from_user.id):
            return bot.reply_to(message, "⛔️ No tienes permisos para acceder a este panel.")
        show_admin_menu(bot, message.chat.id)

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📦 Crear configuración")
    def start_create_config(message):
        bot.send_message(
            message.chat.id,
            "🧾 Escribe un *nombre único* para el cliente (sin espacios ni símbolos):",
            parse_mode="Markdown"
        )
        ADMIN_FLOW[message.from_user.id] = {'step': 'awaiting_name'}

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in ADMIN_FLOW and ADMIN_FLOW[m.from_user.id]['step'] == 'awaiting_name')
    def ask_plan(message):
        client_name = message.text.strip()
        if " " in client_name or not client_name.isalnum():
            return bot.reply_to(message, "⚠️ Nombre inválido. Usa solo letras y números, sin espacios ni símbolos.")

        ADMIN_FLOW[message.from_user.id]['client_name'] = client_name

        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for plan in PLANES:
            kb.add(KeyboardButton(plan))
        bot.send_message(
            message.chat.id,
            "🕐 Selecciona un *plan de vencimiento* para esta configuración:",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        ADMIN_FLOW[message.from_user.id]['step'] = 'awaiting_plan'

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in ADMIN_FLOW and ADMIN_FLOW[m.from_user.id]['step'] == 'awaiting_plan')
    def generate_configuration(message):
        plan = message.text.strip()
        if plan not in PLANES_PRECIOS:
            return bot.reply_to(message, "❌ Plan inválido. Selecciona una opción del teclado.")

        data = ADMIN_FLOW.pop(message.from_user.id)
        client_name = data['client_name']

        # Generar claves e IP
        private_key, public_key = generate_keypair()
        ip = get_next_available_ip()
        if not ip:
            return bot.send_message(message.chat.id, "❌ No hay IPs disponibles en este momento.")

        # Crear archivo .conf
        path = generate_conf(client_name, private_key, ip, SERVER_PUBLIC_IP)

        if not path or not os.path.exists(path):
            return bot.send_message(message.chat.id, "⚠️ Error al generar el archivo. Verifica permisos o rutas.")

        qr_image = generate_qr_code(path)

        # Calcular vencimiento
        if "dias" in PLANES_PRECIOS[plan]:
            vencimiento = datetime.utcnow() + timedelta(days=PLANES_PRECIOS[plan]["dias"])
        elif "horas" in PLANES_PRECIOS[plan]:
            vencimiento = datetime.utcnow() + timedelta(hours=PLANES_PRECIOS[plan]["horas"])
        else:
            vencimiento = datetime.utcnow() + timedelta(days=15)

        # Guardar en archivo
        users = load_users()
        users[client_name] = {
            "ip": ip,
            "public_key": public_key,
            "vencimiento": vencimiento.isoformat(),
            "plan": plan
        }
        save_users(users)

        bot.send_message(
            message.chat.id,
            f"✅ Configuración generada para: <b>{client_name}</b>\n📅 Vence el: <b>{vencimiento.strftime('%Y-%m-%d %H:%M')} UTC</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

        try:
            with open(path, "rb") as f:
                bot.send_document(message.chat.id, f)
            bot.send_photo(message.chat.id, qr_image, caption="📲 Escanea este código QR para importar la configuración.")
        except Exception as e:
            bot.send_message(message.chat.id, f"⚠️ Error al enviar archivos:\n<code>{e}</code>", parse_mode="HTML")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🗑 Eliminar configuración")
    def delete_config_prompt(message):
        users = load_users()
        if not users:
            return bot.send_message(message.chat.id, "ℹ️ No hay configuraciones activas registradas.")

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for name in users:
            kb.add(KeyboardButton(name))
        bot.send_message(message.chat.id, "❌ Selecciona la configuración que deseas eliminar:", reply_markup=kb)
        ADMIN_FLOW[message.from_user.id] = {'step': 'awaiting_delete'}

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.from_user.id in ADMIN_FLOW and ADMIN_FLOW[m.from_user.id]['step'] == 'awaiting_delete')
    def delete_config(message):
        client_name = message.text.strip()
        users = load_users()
        if client_name not in users:
            return bot.reply_to(message, "⚠️ El nombre ingresado no existe.")

        delete_conf(client_name)
        del users[client_name]
        save_users(users)

        bot.send_message(
            message.chat.id,
            f"✅ Configuración <b>{client_name}</b> eliminada correctamente.",
            reply_markup=ReplyKeyboardRemove(),
            parse_mode="HTML"
        )
        ADMIN_FLOW.pop(message.from_user.id)

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🔙 Salir")
    def salir_admin(message):
        bot.send_message(message.chat.id, "👋 Has salido del panel.", reply_markup=ReplyKeyboardRemove())

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id))
    def fallback_admin(message):
        if message.from_user.id not in ADMIN_FLOW:
            show_admin_menu(bot, message.chat.id)

# Menú visual persistente del administrador
def show_admin_menu(bot: TeleBot, chat_id: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📦 Crear configuración"))
    kb.add(KeyboardButton("🗑 Eliminar configuración"))
    kb.add(KeyboardButton("🔙 Salir"))
    bot.send_message(
        chat_id,
        "🔧 <b>Panel de Administrador</b>\n\nSelecciona una opción:",
        reply_markup=kb,
        parse_mode="HTML"
            )
