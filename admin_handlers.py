# admin_handlers.py

from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from config import ADMIN_ID, PLANES, PLANES_PRECIOS
from storage import load_users, save_users
from utils import generate_wg_config, generate_qr_code, delete_conf
from datetime import datetime, timedelta
import os

ADMIN_FLOW = {}  # Almacena pasos del flujo activo por admin

def is_admin(user_id):
    return user_id == ADMIN_ID

def register_admin_handlers(bot: TeleBot):

    @bot.message_handler(commands=['admin', 'start'])
    def handle_admin(message):
        if is_admin(message.from_user.id):
            show_admin_menu(bot, message.chat.id)
        else:
            bot.reply_to(message, "⛔️ No tienes permisos para acceder a este panel.")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📦 Crear configuración")
    def start_create_config(message):
        bot.send_message(
            message.chat.id,
            "🧾 Escribe un *nombre único* para el cliente (sin espacios ni símbolos):",
            parse_mode="Markdown"
        )
        ADMIN_FLOW[message.from_user.id] = {'step': 'awaiting_name'}

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and ADMIN_FLOW.get(m.from_user.id, {}).get('step') == 'awaiting_name')
    def ask_plan(message):
        client_name = message.text.strip()
        if " " in client_name or not client_name.isalnum():
            return bot.reply_to(message, "⚠️ Nombre inválido. Usa solo letras y números, sin espacios ni símbolos.")

        ADMIN_FLOW[message.from_user.id]['client_name'] = client_name

        kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        for plan in PLANES:
            emoji = "💼" if "pro" in plan.lower() else "🎁" if "trial" in plan.lower() else "🕐"
            kb.add(KeyboardButton(f"{emoji} {plan}"))
        kb.add(KeyboardButton("🔙 Volver"))

        bot.send_message(
            message.chat.id,
            "🕐 Selecciona un *plan de vencimiento* para esta configuración:",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        ADMIN_FLOW[message.from_user.id]['step'] = 'awaiting_plan'

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and ADMIN_FLOW.get(m.from_user.id, {}).get('step') == 'awaiting_plan')
    def generate_configuration(message):
        if message.text == "🔙 Volver":
            ADMIN_FLOW.pop(message.from_user.id, None)
            return show_admin_menu(bot, message.chat.id)

        plan = message.text.replace("💼", "").replace("🎁", "").replace("🕐", "").strip()
        if plan not in PLANES_PRECIOS:
            return bot.reply_to(message, "❌ Plan inválido. Selecciona una opción del teclado.")

        data = ADMIN_FLOW.pop(message.from_user.id)
        client_name = data['client_name']

        dias = PLANES_PRECIOS[plan].get('dias')
        horas = PLANES_PRECIOS[plan].get('horas')

        if dias:
            vencimiento = datetime.utcnow() + timedelta(days=dias)
        elif horas:
            vencimiento = datetime.utcnow() + timedelta(hours=horas)
        else:
            return bot.send_message(message.chat.id, "⚠️ Error: plan sin duración definida.")

        try:
            path = generate_wg_config(client_name, vencimiento.strftime('%Y-%m-%d %H:%M:%S'), plan)
            qr_image = generate_qr_code(path)
        except ValueError as e:
            return bot.send_message(message.chat.id, f"⚠️ Error: {str(e)}")
        except RuntimeError as e:
            return bot.send_message(message.chat.id, f"❌ {str(e)}")

        bot.send_message(
            message.chat.id,
            f"✅ Configuración generada para: <b>{client_name}</b>\n📅 Vence: <b>{vencimiento.strftime('%Y-%m-%d %H:%M')}</b>",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )

        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f)

        bot.send_photo(message.chat.id, qr_image, caption="📲 Escanea este código QR en tu app WireGuard")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🗑 Eliminar configuración")
    def eliminar_config_prompt(message):
        users = load_users()
        if not users:
            return bot.send_message(message.chat.id, "ℹ️ No hay configuraciones registradas.")

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        for name in users:
            kb.add(KeyboardButton(name))
        bot.send_message(message.chat.id, "❌ Selecciona una configuración para eliminar:", reply_markup=kb)
        ADMIN_FLOW[message.from_user.id] = {'step': 'awaiting_delete'}

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and ADMIN_FLOW.get(m.from_user.id, {}).get('step') == 'awaiting_delete')
    def eliminar_config(message):
        client_name = message.text.strip()
        users = load_users()
        if client_name not in users:
            return bot.reply_to(message, "⚠️ Nombre inválido.")

        delete_conf(client_name)
        users.pop(client_name)
        save_users(users)

        bot.send_message(
            message.chat.id,
            f"✅ Configuración <b>{client_name}</b> eliminada correctamente.",
            parse_mode="HTML",
            reply_markup=ReplyKeyboardRemove()
        )
        ADMIN_FLOW.pop(message.from_user.id)

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📄 Ver configuraciones activas")
    def ver_configuraciones(message):
        users = load_users()
        if not users:
            return bot.send_message(message.chat.id, "ℹ️ No hay configuraciones activas.")

        texto = "<b>📋 Configuraciones activas:</b>\n"
        for nombre, datos in users.items():
            texto += f"\n🔸 <b>{nombre}</b> — IP: {datos['ip']}\n⏳ Vence: {datos['vencimiento']}\n"

        bot.send_message(message.chat.id, texto, parse_mode="HTML")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📊 Ver estadísticas")
    def ver_estadisticas(message):
        users = load_users()
        total = len(users)
        planes = {}
        for datos in users.values():
            p = datos['plan']
            planes[p] = planes.get(p, 0) + 1

        texto = f"📊 <b>Estadísticas:</b>\n\n👥 Total clientes: <b>{total}</b>\n"
        for plan, count in planes.items():
            texto += f"🔹 {plan}: {count}\n"

        bot.send_message(message.chat.id, texto, parse_mode="HTML")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "📁 Respaldar datos (.json)")
    def enviar_respaldo(message):
        path = os.path.join("data", "users.json")
        if not os.path.exists(path):
            return bot.send_message(message.chat.id, "⚠️ Archivo de usuarios no encontrado.")

        with open(path, "rb") as f:
            bot.send_document(message.chat.id, f, caption="📁 Archivo JSON de respaldo")

    @bot.message_handler(func=lambda m: is_admin(m.from_user.id) and m.text == "🔙 Salir")
    def salir_panel(message):
        bot.send_message(message.chat.id, "🔽 Teclado ocultado.", reply_markup=ReplyKeyboardRemove())

def show_admin_menu(bot: TeleBot, chat_id: int):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("📦 Crear configuración"))
    kb.add(KeyboardButton("🗑 Eliminar configuración"))
    kb.add(KeyboardButton("📄 Ver configuraciones activas"))
    kb.add(KeyboardButton("📊 Ver estadísticas"))
    kb.add(KeyboardButton("📁 Respaldar datos (.json)"))
    kb.add(KeyboardButton("🔙 Salir"))

    bot.send_message(
        chat_id,
        "🔧 <b>Panel de Administrador</b>\n\nSelecciona una opción para gestionar WireGuard:",
        reply_markup=kb,
        parse_mode="HTML"
        )
