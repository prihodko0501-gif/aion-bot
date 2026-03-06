from bot.api import send_message
from bot.keyboards import *
from bot import texts
from core.biotime import calculate_biotime


USER_STATE = {}


def handle_update(update):

    message = update.get("message") or {}

    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return

    if text == "/start":

        USER_STATE.pop(chat_id, None)

        send_message(
            chat_id,
            texts.WELCOME_TEXT,
            reply_markup=main_menu_reply()
        )
        return

    if USER_STATE.get(chat_id, {}).get("step") == "biotime_input":

        parts = text.split()

        if len(parts) != 6:
            send_message(
                chat_id,
                "Нужно 6 чисел. Пример: 7 6 8 0 0 1",
                reply_markup=main_menu_reply()
            )
            return

        try:

            sleep = float(parts[0])
            stress = float(parts[1])
            recovery = float(parts[2])
            pressure_penalty = float(parts[3])
            drop_penalty = float(parts[4])
            risk_penalty = float(parts[5])

        except Exception:

            send_message(
                chat_id,
                "Ошибка формата. Введи 6 чисел через пробел.",
                reply_markup=main_menu_reply()
            )
            return

        biotime, level, advice = calculate_biotime(
            sleep,
            stress,
            recovery,
            pressure_penalty,
            drop_penalty,
            risk_penalty
        )

        send_message(
            chat_id,
            f"🧬 BioTime = {biotime}\n{level}\n\nРекомендация: {advice}",
            reply_markup=main_menu_reply()
        )

        USER_STATE.pop(chat_id, None)

        return

    if text == BTN_BIOTIME:

        USER_STATE[chat_id] = {"step": "biotime_input"}

        send_message(
            chat_id,
            texts.BIOTIME_INPUT,
            reply_markup=main_menu_reply()
        )

        return

    if text == BTN_SLEEP:

        send_message(chat_id, "💤 Sleep модуль.", reply_markup=main_menu_reply())
        return

    if text == BTN_CNS:

        send_message(chat_id, "🧠 CNS модуль.", reply_markup=main_menu_reply())
        return

    if text == BTN_RECOVERY:

        send_message(chat_id, "🔥 Recovery модуль.", reply_markup=main_menu_reply())
        return

    if text == BTN_PRESSURE:

        send_message(chat_id, "❤️ Pressure модуль.", reply_markup=main_menu_reply())
        return

    if text == BTN_INFO:

        send_message(
            chat_id,
            "ℹ️ AION\n\n"
            "🧬 BioTime — интегральная оценка восстановления\n"
            "❤️ Pressure — давление\n"
            "💤 Sleep — сон\n"
            "🧠 CNS — нервная система\n"
            "🔥 Recovery — восстановление",
            reply_markup=main_menu_reply()
        )
        return

    send_message(chat_id, "Выберите модуль:", reply_markup=main_menu_reply())