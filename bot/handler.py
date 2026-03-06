from bot.api import send_message, edit_message, answer_callback_query
from bot.keyboards import main_menu, back_to_menu
import bot.texts as texts


def handle_update(update):
    try:
        if "callback_query" in update:
            handle_callback(update["callback_query"])
            return

        if "message" in update:
            handle_message(update["message"])
            return

        print("UNKNOWN UPDATE:", update)

    except Exception as e:
        print("HANDLE_UPDATE ERROR:", str(e))


def handle_message(message):
    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    if text in ["/start", "start", "старт", "Start", "START"]:
        send_message(
            chat_id=chat_id,
            text=texts.WELCOME_TEXT,
            reply_markup=main_menu()
        )
        return

    send_message(
        chat_id=chat_id,
        text="Используй меню ниже.",
        reply_markup=main_menu()
    )


def handle_callback(callback):
    callback_id = callback["id"]
    data = callback.get("data", "")
    message = callback.get("message", {})
    chat_id = message["chat"]["id"]
    message_id = message["message_id"]

    answer_callback_query(callback_id)

    if data == "menu":
        safe_edit(chat_id, message_id, texts.WELCOME_TEXT, main_menu())
        return

    if data == "new_calc":
        safe_edit(chat_id, message_id, texts.NEW_CALC_TEXT, back_to_menu())
        return

    if data == "nav":
        safe_edit(chat_id, message_id, texts.NAV_TEXT, back_to_menu())
        return

    if data == "dynamics":
        safe_edit(chat_id, message_id, texts.DYNAMICS_TEXT, back_to_menu())
        return

    if data == "history":
        safe_edit(chat_id, message_id, texts.HISTORY_TEXT, back_to_menu())
        return

    if data == "profile":
        safe_edit(chat_id, message_id, texts.PROFILE_TEXT, back_to_menu())
        return

    if data == "settings":
        safe_edit(chat_id, message_id, texts.SETTINGS_TEXT, back_to_menu())
        return

    if data == "about":
        safe_edit(chat_id, message_id, texts.ABOUT_TEXT, back_to_menu())
        return

    safe_edit(chat_id, message_id, "Неизвестная команда.", main_menu())


def safe_edit(chat_id, message_id, text, reply_markup=None):
    result = edit_message(chat_id, message_id, text, reply_markup)
    if not result.get("ok"):
        send_message(chat_id, text, reply_markup)