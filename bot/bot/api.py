import os
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}" if TELEGRAM_TOKEN else None


def api_post(method: str, payload: dict, timeout: int = 20):
    if not API_URL:
        print("TG: API_URL is None (no TELEGRAM_TOKEN?)")
        return None
    try:
        r = requests.post(f"{API_URL}/{method}", json=payload, timeout=timeout)
    except Exception as e:
        print("TG EXC:", repr(e))
        return None

    try:
        data = r.json()
    except Exception:
        print("TG BAD JSON:", r.status_code, (r.text or "")[:500])
        return None

    if data.get("ok"):
        return data

    desc = (data.get("description") or "").lower()
    if "message is not modified" in desc:
        return {"ok": True}

    print("TG ERROR:", r.status_code, data)
    return data


def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = api_post("sendMessage", payload)
    if data and data.get("ok") and data.get("result"):
        return data["result"]["message_id"]
    return None


def edit_message(chat_id: int, message_id: int, text: str, reply_markup=None) -> bool:
    payload = {"chat_id": chat_id, "message_id": message_id, "text": text}
    if reply_markup is not None:
        payload["reply_markup"] = reply_markup
    data = api_post("editMessageText", payload)

    if not data:
        return False
    if data.get("ok"):
        return True

    desc = (data.get("description") or "").lower()
    return "message is not modified" in desc


def delete_message(chat_id: int, message_id: int):
    api_post("deleteMessage", {"chat_id": chat_id, "message_id": message_id})


def try_delete_user_message(chat_id: int, message_id):
    if not message_id:
        return
    try:
        delete_message(chat_id, message_id)
    except Exception:
        pass


def answer_callback(callback_query_id: str):
    api_post("answerCallbackQuery", {"callback_query_id": callback_query_id})
