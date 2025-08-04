# notifications.py

from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from config import ADMIN_ID, AVISOS_VENCIMIENTO_HORAS
from storage import load_users
from telebot import TeleBot

def check_expirations(bot: TeleBot):
    """
    Verifica periódicamente si hay configuraciones que están por vencer
    y notifica al administrador.
    """
    while True:
        try:
            users = load_users()
            now = datetime.utcnow()
            for name, data in users.items():
                vencimiento = datetime.fromisoformat(data["vencimiento"])
                restante = vencimiento - now

                for horas in AVISOS_VENCIMIENTO_HORAS:
                    aviso = timedelta(hours=horas)
                    margen = timedelta(minutes=5)

                    if abs(restante - aviso) <= margen:
                        bot.send_message(
                            ADMIN_ID,
                            f"⚠️ <b>Aviso de vencimiento</b>\n\n"
                            f"📛 Cliente: <b>{name}</b>\n"
                            f"🕒 Tiempo restante: <b>{int(restante.total_seconds() // 3600)} horas</b>\n"
                            f"📅 Vence: <b>{vencimiento.strftime('%Y-%m-%d %H:%M')} UTC</b>",
                            parse_mode="HTML"
                        )
        except Exception as e:
            print(f"[ERROR] En notificación de vencimiento: {e}")
        
        sleep(300)  # Revisión cada 5 minutos

def start_notifier(bot: TeleBot):
    """
    Inicia el sistema de notificaciones automáticas en un hilo separado.
    """
    t = Thread(target=check_expirations, args=(bot,), daemon=True)
    t.start()
