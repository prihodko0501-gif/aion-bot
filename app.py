import os
import requests
from flask import Flask, request

app = Flask(__name__)

TOKEN = os.getenv("TELEGRAM_TOKEN")
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"


# -------------------------
# AION: Формулы (сегодняшние)
# -------------------------
def clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def score_sleep(hours: float) -> float:
    # Формула дня: базовая оценка сна (идеал 8ч)
    # 8ч -> 100, 6ч -> 75, 5ч -> 60, 9ч -> 95 (чуть ниже, чем 8)
    if hours <= 0:
        return 0
    if hours <= 8:
        return clamp(50 + (hours / 8) * 50)  # 0..8 -> 50..100
    # лёгкий штраф за “пересон”
    return clamp(100 - (hours - 8) * 5)     # 9 -> 95, 10 -> 90


def score_stress(level_0_10: float) -> float:
    # Формула дня: стресс 0..10 превращаем в 0..100 (чем меньше стресс — тем лучше)
    # 0 -> 100, 10 -> 0
    return clamp(100 - (level_0_10 * 10))


def score_pressure(sys: float, dia: float) -> float:
    # Формула дня: давление. Идеал ~120/80.
    # Чем дальше от идеала — тем ниже балл.
    ideal_sys, ideal_dia = 120.0, 80.0
    dist = abs(sys - ideal_sys) + abs(dia - ideal_dia)
    return clamp(100 - dist)  # грубо: dist 20 -> 80, dist 40 -> 60


def aion_recovery(sleep_score: float, stress_score: float, pressure_score: float) -> float:
    # Формула дня: Recovery (веса можно менять)
    # Сон 45% / Стресс 35% / Давление 20%
    return clamp(0.45 * sleep_score + 0.35 * stress_score + 0.20 * pressure_score)


def aion_biotime(recovery: float) -> float:
    # Формула дня: BioTime / WearRate (индикатор “износа”, где выше — лучше)
    # Здесь просто “витрина”: BioTime = Recovery
    # (если у тебя есть своя формула BioTime — скажешь, я заменю)
    return clamp(recovery)


# -------------------------
# Telegram helpers
# -------------------------
def send_message(chat_id: int, text: str):
    r = requests.post(f"{BASE_URL}/sendMessage", json={"chat_id": chat_id, "text": text})
    print("sendMessage:", r.status_code, r.text)


# -------------------------
# Routes
# -------------------------
@app.route("/")
def home():
    return "AION is alive 🚀"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True) or {}
    message = data.get("message") or data.get("edited_message")
    if not message:
        return "ok"

    chat_id = message["chat"]["id"]
    text = (message.get("text") or "").strip()

    # /start
    if text == "/start":
        msg = (
            "🤖 *AION Bot активирован* ✅\n\n"
            "Команды:\n"
            "🚀 /aion — быстрый расчёт (сон/стресс/давление)\n"
            "🧠 /help — помощь\n\n"
            "Формат для /aion:\n"
            "`/aion sleep=7.5 stress=3 bp=128/82`\n\n"
            "⚡️ Готов принимать данные."
        )
        # Telegram plain text, без Markdown-парсинга чтобы не ловить ошибки
        send_message(chat_id, msg.replace("*", "").replace("`", ""))
        return "ok"

    # /help
    if text == "/help":
        msg = (
            "🧠 *AION Help*\n\n"
            "1) Быстрый ввод:\n"
            "👉 /aion sleep=7.5 stress=3 bp=128/82\n\n"
            "2) Что значит:\n"
            "😴 sleep — часы сна\n"
            "🔥 stress — стресс 0..10 (0 спокойно, 10 максимум)\n"
            "🩸 bp — давление SYS/DIA\n\n"
            "3) Что выдаём:\n"
            "✅ SleepScore / StressScore / PressureScore\n"
            "💪 Recovery\n"
            "🧬 BioTime\n"
        )
        send_message(chat_id, msg.replace("*", ""))
        return "ok"

    # /aion sleep=.. stress=.. bp=../..
    if text.startswith("/aion"):
        try:
            # дефолты
            sleep_h = None
            stress = None
            sys = None
            dia = None

            parts = text.replace("/aion", "").strip().split()
            for p in parts:
                if p.startswith("sleep="):
                    sleep_h = float(p.split("=", 1)[1])
                elif p.startswith("stress="):
                    stress = float(p.split("=", 1)[1])
                elif p.startswith("bp="):
                    bp = p.split("=", 1)[1]
                    sys_s, dia_s = bp.split("/", 1)
                    sys = float(sys_s)
                    dia = float(dia_s)

            if sleep_h is None or stress is None or sys is None or dia is None:
                send_message(chat_id, "⚠️ Формат неверный. Пример:\n/aion sleep=7.5 stress=3 bp=128/82")
                return "ok"

            s_sleep = score_sleep(sleep_h)
            s_stress = score_stress(stress)
            s_bp = score_pressure(sys, dia)
            rec = aion_recovery(s_sleep, s_stress, s_bp)
            bio = aion_biotime(rec)

            msg = (
                "📊 *AION • Расчёт дня* ✅\n\n"
                f"😴 Сон: {sleep_h} ч → SleepScore: {s_sleep:.1f}\n"
                f"🔥 Стресс: {stress}/10 → StressScore: {s_stress:.1f}\n"
                f"🩸 Давление: {int(sys)}/{int(dia)} → PressureScore: {s_bp:.1f}\n\n"
                f"💪 Recovery: {rec:.1f}\n"
                f"🧬 BioTime: {bio:.1f}\n\n"
                "⚡️ Хочешь — добавим ещё: HRV, пульс, шаги, тренировки, питание."
            )
            send_message(chat_id, msg.replace("*", ""))
            return "ok"

        except Exception as e:
            print("AION parse error:", e)
            send_message(chat_id, "❌ Ошибка обработки. Проверь формат:\n/aion sleep=7.5 stress=3 bp=128/82")
            return "ok"

    # default
    send_message(chat_id, "👋 Напиши /start или /aion sleep=7.5 stress=3 bp=128/82")
    return "ok"


if __name__ == "__main__":
    # локально
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
    
 