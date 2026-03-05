from bot.api import send_message, edit_message, answer_callback
from bot.keyboards import main_menu_inline, back_inline, CB_MENU
from bot.texts import start_text

# Временно: простое состояние в памяти.
# Когда подключим database/state.py — заменим.
MEM_UI = {}


def ensure_ui(chat_id: int):
    mid = MEM_UI.get(chat_id)
    if mid:
        ok = edit_message(chat_id, mid, start_text(), main_menu_inline())
        if ok:
            return mid
    new_mid = send_message(chat_id, start_text(), main_menu_inline())
    if new_mid:
        MEM_UI[chat_id] = new_mid
    return new_mid


def handle_update(update: dict):
    # CALLBACKS
    if "callback_query" in update:
        cq = update["callback_query"]
        if cq.get("id"):
            answer_callback(cq["id"])

        msg = cq.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        message_id = msg.get("message_id")
        data = cq.get("data")

        if not chat_id or not message_id:
            return

        if data == CB_MENU:
            edit_message(chat_id, message_id, start_text(), main_menu_inline())
        return

    # TEXT
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    if not chat_id:
        return

    text = (message.get("text") or "").strip().lower()
    if text in ("/start", "/menu", "start", "старт"):
        ensure_ui(chat_id)
        return

    ensure_ui(chat_id)
