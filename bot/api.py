import os
import requests

TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TOKEN}"


def tg_request(method, payload):
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=15)
        return r.json()
    except Exception as e:
        print("TG REQUEST ERROR:", e)
        return {"ok": False, "error": str(e)}


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return tg_request("sendMessage", payload)


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    return tg_request("editMessageText", payload)


def answer_callback_query(callback_query_id, text=None):
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    return tg_request("answerCallbackQuery", payload)


def remove_reply_keyboard(chat_id, text="Старая клавиатура удалена"):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "reply_markup": {
            "remove_keyboard": True
        }
    }
    return tg_request("sendMessage", payload)