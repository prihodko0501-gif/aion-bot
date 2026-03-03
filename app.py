import os
import logging
import requests
from flask import Flask, request

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN env var is missing")

TG_API = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

def tg(method: str, payload: dict):
    r = requests.post(f"{TG_API}/{method}", json=payload, timeout=20)
    try:
        j = r.json()
    except Exception:
        j = {"ok": False, "raw": r.text}
    if not r.ok or not j.get("ok"):
        logging.error("TG %s failed: status=%s resp=%s payload=%s", method, r.status_code, j, payload)
    return j

def menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🧬 BioTime", "callback_data": "module:biotime"}],
            [
                {"text": "💤 Sleep", "callback_data": "module:sleep"},
                {"text": "🧠 CNS", "callback_data": "module:cns"},
            ],
            [
                {"text": "🔥 Recovery", "callback_data": "module:recovery"},
                {"text": "❤️ Pressure", "callback_data": "module:pressure"},
            ],
            [{"text": "ℹ️ Info", "callback_data": "info"}],
        ]
    }

def send_menu(chat_id: int):
    tg("sendMessage", {
        "chat_id": chat_id,
        "text": "AION — система управления скоростью биологического износа.\n\nВыберите модуль:",
        "reply_markup": menu_keyboard()
    })

@app.route("/", methods=["GET"])
def health():
    return "ok", 200

@app.route("/", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=False)

    # Логируем тип апдейта
    logging.info("UPDATE keys=%s", list(update.keys()))

    # 1) обычные сообщения
    if "message" in update:
        msg = update["message"]
        chat_id = msg["chat"]["id"]
        text = msg.get("text", "")

        logging.info("MESSAGE chat_id=%s text=%r", chat_id, text)

        if text == "/start":
            send_menu(chat_id)
        else:
            tg("sendMessage", {
                "chat_id": chat_id,
                "text": "Напиши /start чтобы открыть меню."
            })

        return "ok", 200

    # 2) нажатия кнопок (callback_query)
    if "callback_query" in update:
        cb = update["callback_query"]
        cb_id = cb["id"]
        data = cb.get("data", "")
        chat_id = cb["message"]["chat"]["id"]

        logging.info("CALLBACK chat_id=%s data=%r", chat_id, data)

        # ВАЖНО: всегда отвечаем на callback, иначе телега “крутит”
        tg("answerCallbackQuery", {
            "callback_query_id": cb_id
        })

        # Роутинг по data
        if data.startswith("module:"):
            module = data.split(":", 1)[1]

            if module == "biotime":
                tg("sendMessage", {"chat_id": chat_id, "text": "🧬 BioTime открыт. Отправь: возраст, рост, вес (пример: 36, 182, 86)."})
            elif module == "sleep":
                tg("sendMessage", {"chat_id": chat_id, "text": "💤 Sleep — пока пусто."})
            elif module == "cns":
                tg("sendMessage", {"chat_id": chat_id, "text": "🧠 CNS — пока пусто."})
            elif module == "recovery":
                tg("sendMessage", {"chat_id": chat_id, "text": "🔥 Recovery — пока пусто."})
            elif module == "pressure":
                tg("sendMessage", {"chat_id": chat_id, "text": "❤️ Pressure — пока пусто."})
            else:
                tg("sendMessage", {"chat_id": chat_id, "text": f"Неизвестный модуль: {module}"})

        elif data == "info":
            tg("sendMessage", {"chat_id": chat_id, "text": "ℹ️ AION — Biological Upgrade System."})

        else:
            tg("sendMessage", {"chat_id": chat_id, "text": f"Нераспознанная кнопка: {data}"})

        return "ok", 200

    # если прилетело что-то иное
    logging.warning("UNKNOWN UPDATE: %s", update)
    return "ok", 200