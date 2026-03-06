import os
import requests

TOKEN = os.environ.get("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}" if TOKEN else None


def send_message(chat_id, text, reply_markup=None):
    if not BASE_URL:
        return None

    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=20)

    try:
        data = r.json()
    except Exception:
        return None

    if data.get("ok"):
        return data["result"]["message_id"]

    return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    if not BASE_URL:
        return False

    payload = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }

    if reply_markup is not None:
        payload["reply_markup"] = reply_markup

    r = requests.post(f"{BASE_URL}/editMessageText", json=payload, timeout=20)

    try:
        data = r.json()
    except Exception:
        return False

    if data.get("ok"):
        return True

    description = (data.get("description") or "").lower()
    if "message is not modified" in description:
        return True

    return False


def try_delete_user_message(chat_id, message_id):
    if not BASE_URL:
        return

    try:
        requests.post(
            f"{BASE_URL}/deleteMessage",
            json={"chat_id": chat_id, "message_id": message_id},
            timeout=20,
        )
    except Exception:
        pass


def answer_callback(callback_query_id):
    if not BASE_URL:
        return

    try:
        requests.post(
            f"{BASE_URL}/answerCallbackQuery",
            json={"callback_query_id": callback_query_id},
            timeout=20,
        )
    except Exception:
        pass


def send_document_bytes(chat_id, filename, data):
    if not BASE_URL:
        return

    files = {
        "document": (filename, data)
    }

    requests.post(
        f"{BASE_URL}/sendDocument",
        data={"chat_id": chat_id},
        files=files,
        timeout=30,
    )