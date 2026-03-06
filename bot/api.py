import os
import requests

TOKEN = os.environ.get("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text, reply_markup=None):
    url = f"{BASE_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    r = requests.post(url, json=payload, timeout=20)
    data = r.json()

    if data.get("ok"):
        return data["result"]["message_id"]
    return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"{BASE_URL}/editMessageText"
    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    r = requests.post(url, json=payload, timeout=20)
    try:
        data = r.json()
        return data.get("ok", False)
    except Exception:
        return False


def try_delete_user_message(chat_id, message_id):
    try:
        requests.post(
            f"{BASE_URL}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id},
            timeout=20,
        )
    except Exception:
        pass


def answer_callback(callback_query_id):
    requests.post(
        f"{BASE_URL}/answerCallbackQuery",
        json={"callback_query_id": callback_query_id},
        timeout=20,
    )


def send_document_bytes(chat_id, filename, data):
    files = {
        "document": (filename, data)
    }
    requests.post(
        f"{BASE_URL}/sendDocument",
        data={"chat_id": chat_id},
        files=files,
        timeout=30,
    )