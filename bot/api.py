import requests
import os

TOKEN = os.environ.get("BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"


def send_message(chat_id, text, reply_markup=None):
    r = requests.post(
        f"{BASE}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "reply_markup": reply_markup
        }
    )
    try:
        return r.json()["result"]["message_id"]
    except:
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    requests.post(
        f"{BASE}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "reply_markup": reply_markup
        }
    )
    return True


def try_delete_user_message(chat_id, message_id):
    try:
        requests.post(
            f"{BASE}/deleteMessage",
            json={
                "chat_id": chat_id,
                "message_id": message_id
            }
        )
    except:
        pass


def answer_callback(callback_query_id):
    requests.post(
        f"{BASE}/answerCallbackQuery",
        json={
            "callback_query_id": callback_query_id
        }
    )


def send_document_bytes(chat_id, filename, data):
    files = {
        "document": (filename, data)
    }

    requests.post(
        f"{BASE}/sendDocument",
        data={"chat_id": chat_id},
        files=files
    )
