import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")

BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


def tg_request(method, payload):
    url = f"{BASE_URL}/{method}"
    r = requests.post(url, json=payload)
    try:
        return r.json()
    except Exception:
        return {"ok": False}


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    return tg_request("sendMessage", payload)


def edit_message(chat_id, message_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }

    if reply_markup:
        payload["reply_markup"] = reply_markup

    return tg_request("editMessageText", payload)


def answer_callback_query(callback_query_id):
    payload = {"callback_query_id": callback_query_id}
    return tg_request("answerCallbackQuery", payload)