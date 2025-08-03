# notifications.py

from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from config import ADMINS, VENCIMIENTO_AVISOS_HORAS
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

                for horas in VENCIMIENTO_AVISOS_HORAS:
                    aviso = timedelta(hours=horas)
                    margen = timedelta(minutes=5)

                    # Si estamos dentro del margen de aviso
                    if abs(restante - aviso) <= margen:
                        for admin_id in ADMINS:
                            bot.send_message(
                                admin_id,
                                f"⚠️ *Aviso de vencimiento*\n\n"
                                f"📛 Cliente: *{name}*\n"
                                f"🕒 Tiempo restante: {int(restante.total_seconds() // 3600)} horas\n"
                                f"📅 Vence: *{vencimiento.strftime('%Y-%m-%d %H:%M')} UTC*",
                                parse_mode="Markdown"
                            )
        except Exception as e:
            print(f"[ERROR] En notificación de vencimiento: {e}")
        
        sleep(300)  # Revisa cada 5 minutos

def start_notifier(bot: TeleBot):
    """
    Inicia el sistema de notificaciones automáticas en un hilo separado.
    """
    t = Thread(target=check_expirations, args=(bot,), daemon=True)
    t.start()
