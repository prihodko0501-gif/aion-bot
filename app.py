import os
import time
import math
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Простой in-memory state (MVP). На Render при рестарте очистится — это нормально для MVP.
# Формат:
# user_state[user_id] = {"step": "...", "sleep_hours": float, "stress_1_10": int, "sys": int, "dia": int, "pulse": int}
user_state = {}


# ---------- Telegram helpers ----------

def tg_send_message(chat_id: int, text: str, reply_markup: dict | None = None):
    if not BOT_TOKEN:
        return
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)


def main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🛌 Сон", "callback_data": "MOD_SLEEP"}],
            [{"text": "⚡️ Стресс", "callback_data": "MOD_STRESS"}],
            [{"text": "🩺 Давление", "callback_data": "MOD_BP"}],
            [{"text": "🔁 Recovery Index", "callback_data": "MOD_RECOVERY"}],
            [{"text": "ℹ️ О системе AION", "callback_data": "MOD_ABOUT"}],
        ]
    }


def back_to_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "⬅️ Назад в меню", "callback_data": "BACK_MENU"}]
        ]
    }


# ---------- AION logic (MVP) ----------

def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def calc_recovery_index(data: dict) -> int:
    """
    Черновой MVP индекс восстановления 0..100.
    Это НЕ мед.диагностика, просто показатель состояния по введённым данным.
    """

    sleep = data.get("sleep_hours")
    stress = data.get("stress_1_10")
    sys = data.get("sys")
    dia = data.get("dia")
    pulse = data.get("pulse")

    # базовые штрафы
    score = 100.0

    # сон: оптимум 7.5ч, отклонение штрафует
    if isinstance(sleep, (int, float)):
        score -= abs(sleep - 7.5) * 10  # каждые 1ч отклонения -10

    # стресс 1..10: чем выше, тем хуже
    if isinstance(stress, int):
        score -= (stress - 1) * 6  # стресс=1 -> 0, стресс=10 -> -54

    # давление: грубая оценка, штраф за выход из "условно норм"
    if isinstance(sys, int) and isinstance(dia, int):
        if sys > 130:
            score -= (sys - 130) * 0.8
        if sys < 105:
            score -= (105 - sys) * 0.6
        if dia > 85:
            score -= (dia - 85) * 1.0
        if dia < 65:
            score -= (65 - dia) * 0.8

    # пульс: условно оптимум 55-75 (в покое)
    if isinstance(pulse, int):
        if pulse > 80:
            score -= (pulse - 80) * 1.2
        if pulse < 50:
            score -= (50 - pulse) * 1.0

    score = clamp(score, 0, 100)
    return int(round(score))


def format_summary(uid: int) -> str:
    s = user_state.get(uid, {})
    lines = ["<b>AION — сводка данных</b>"]
    if "sleep_hours" in s:
        lines.append(f"🛌 Сон: <b>{s['sleep_hours']}</b> ч")
    if "stress_1_10" in s:
        lines.append(f"⚡️ Стресс: <b>{s['stress_1_10']}</b>/10")
    if "sys" in s and "dia" in s:
        lines.append(f"🩺 Давление: <b>{s['sys']}/{s['dia']}</b>")
    if "pulse" in s:
        lines.append(f"❤️ Пульс: <b>{s['pulse']}</b>")

    idx = calc_recovery_index(s)
    lines.append("")
    lines.append(f"🔁 Recovery Index: <b>{idx}/100</b>")

    # небольшая интерпретация
    if idx >= 80:
        hint = "Сильное восстановление. Можно работать/тренироваться, но без перегруза."
    elif idx >= 60:
        hint = "Норм. Следи за сном и стрессом, нагрузку держи умеренной."
    elif idx >= 40:
        hint = "Просадка. Лучше восстановление: сон/питание/легкая активность."
    else:
        hint = "Красная зона. Восстановление приоритет. Если есть симптомы — к врачу."

    lines.append(f"🧠 Комментарий: {hint}")
    lines.append("")
    lines.append("<i>AION — это система управления биологическим возрастом через сон, стресс, давление и восстановление.</i>")
    return "\n".join(lines)


# ---------- Routing / Webhook ----------

@app.get("/")
def home():
    return "AION bot is running ✅", 200


@app.post("/telegram")
def telegram_webhook():
    update = request.get_json(silent=True) or {}

    # 1) Callback кнопки
    if "callback_query" in update:
        cq = update["callback_query"]
        uid = cq["from"]["id"]
        chat_id = cq["message"]["chat"]["id"]
        data = cq.get("data", "")

        # Инициализация state
        user_state.setdefault(uid, {"step": None})

        # Назад в меню
        if data == "BACK_MENU":
            user_state[uid]["step"] = None
            tg_send_message(
                chat_id,
                "Выбери модуль AION:",
                reply_markup=main_menu_keyboard()
            )
            return jsonify(ok=True)

        # Модули
        if data == "MOD_SLEEP":
            user_state[uid]["step"] = "WAIT_SLEEP"
            tg_send_message(chat_id, "🛌 Сколько часов ты спал? Напиши числом, например: <b>7.5</b>", reply_markup=back_to_menu_keyboard())
            return jsonify(ok=True)

        if data == "MOD_STRESS":
            user_state[uid]["step"] = "WAIT_STRESS"
            tg_send_message(chat_id, "⚡️ Стресс по шкале 1–10? Напиши число, например: <b>6</b>", reply_markup=back_to_menu_keyboard())
            return jsonify(ok=True)

        if data == "MOD_BP":
            user_state[uid]["step"] = "WAIT_BP"
            tg_send_message(chat_id, "🩺 Напиши давление и пульс в формате: <b>120/80 60</b>", reply_markup=back_to_menu_keyboard())
            return jsonify(ok=True)

        if data == "MOD_RECOVERY":
            tg_send_message(chat_id, format_summary(uid), reply_markup=main_menu_keyboard())
            return jsonify(ok=True)

        if data == "MOD_ABOUT":
            text = (
                "<b>AION — Biological Upgrade System</b>\n\n"
                "AION помогает управлять биологическим возрастом через ключевые модули:\n"
                "• сон\n• стресс\n• давление\n• восстановление\n\n"
                "Дальше добавим: дневник, тренировки, нутриенты, графики и персональные протоколы."
            )
            tg_send_message(chat_id, text, reply_markup=main_menu_keyboard())
            return jsonify(ok=True)

        # default
        tg_send_message(chat_id, "Не понял команду. Выбери модуль:", reply_markup=main_menu_keyboard())
        return jsonify(ok=True)

    # 2) Обычные сообщения
    msg = update.get("message") or {}
    if not msg:
        return jsonify(ok=True)

    chat_id = msg["chat"]["id"]
    uid = msg["from"]["id"]
    text = (msg.get("text") or "").strip()

    user_state.setdefault(uid, {"step": None})

    # /start
    if text.startswith("/start"):
        user_state[uid]["step"] = None
        tg_send_message(
            chat_id,
            "AION bot запущен ✅\n\nВыбери модуль:",
            reply_markup=main_menu_keyboard()
        )
        return jsonify(ok=True)

    # Понимание шага (куда ждём ввод)
    step = user_state[uid].get("step")

    # WAIT_SLEEP
    if step == "WAIT_SLEEP":
        try:
            sleep = float(text.replace(",", "."))
            sleep = clamp(sleep, 0, 16)
            user_state[uid]["sleep_hours"] = sleep
            user_state[uid]["step"] = None
            tg_send_message(chat_id, f"🛌 Принято: <b>{sleep}</b> ч\n\nВыбери следующий модуль:", reply_markup=main_menu_keyboard())
        except Exception:
            tg_send_message(chat_id, "Не понял. Напиши число, например: <b>7.5</b>", reply_markup=back_to_menu_keyboard())
        return jsonify(ok=True)

    # WAIT_STRESS
    if step == "WAIT_STRESS":
        try:
            stress = int(text)
            stress = int(clamp(stress, 1, 10))
            user_state[uid]["stress_1_10"] = stress
            user_state[uid]["step"] = None
            tg_send_message(chat_id, f"⚡️ Принято: <b>{stress}</b>/10\n\nВыбери следующий модуль:", reply_markup=main_menu_keyboard())
        except Exception:
            tg_send_message(chat_id, "Напиши число 1–10, например: <b>6</b>", reply_markup=back_to_menu_keyboard())
        return jsonify(ok=True)

    # WAIT_BP
    if step == "WAIT_BP":
        # формат: 120/80 60
        try:
            parts = text.replace(",", ".").split()
            bp = parts[0]
            pulse = int(parts[1]) if len(parts) > 1 else None

            sys_s, dia_s = bp.split("/")
            sys = int(float(sys_s))
            dia = int(float(dia_s))

            user_state[uid]["sys"] = int(clamp(sys, 70, 250))
            user_state[uid]["dia"] = int(clamp(dia, 40, 150))
            if pulse is not None:
                user_state[uid]["pulse"] = int(clamp(pulse, 30, 220))

            user_state[uid]["step"] = None
            tg_send_message(chat_id, "🩺 Принято.\n\n" + format_summary(uid), reply_markup=main_menu_keyboard())
        except Exception:
            tg_send_message(chat_id, "Не понял формат. Напиши так: <b>120/80 60</b>", reply_markup=back_to_menu_keyboard())
        return jsonify(ok=True)

    # Если шага нет — показываем меню
    tg_send_message(chat_id, "Выбери модуль AION:", reply_markup=main_menu_keyboard())
    return jsonify(ok=True)


# ---------- Optional: set webhook endpoint ----------
# Запусти один раз вручную (локально) или сделай отдельный route /set_webhook
@app.post("/set_webhook")
def set_webhook():
    """
    В Render можно дернуть этот endpoint вручную (POST),
    чтобы выставить webhook на текущий домен.
    Требует переменную BASE_URL, например: https://aion-bot.onrender.com
    """
    base = os.environ.get("BASE_URL", "").strip().rstrip("/")
    if not base or not BOT_TOKEN:
        return jsonify(ok=False, error="BASE_URL or TELEGRAM_BOT_TOKEN not set"), 400

    hook_url = f"{base}/telegram"
    r = requests.get(f"{API_URL}/setWebhook", params={"url": hook_url}, timeout=10)
    return jsonify(ok=True, hook_url=hook_url, telegram=r.json())


if __name__ == "__main__":
    # для локального запуска
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))