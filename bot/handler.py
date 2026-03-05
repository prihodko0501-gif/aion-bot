import time
import threading

from bot.api import (
    send_message, edit_message, try_delete_user_message,
    answer_callback, send_document_bytes
)
from bot.keyboards import (
    CB_MENU, CB_INFO, CB_SETTINGS, CB_PROFILE, CB_NEW, CB_NAV, CB_DYNAMICS, CB_HISTORY,
    CB_H7, CB_H14, CB_CSV, CB_ASSIST,
    main_menu_inline, back_inline, history_inline, after_calc_inline
)
from bot.texts import start_text, info_text, settings_text, pro_hint_text

from database.state import get_state, set_state, clear_flow
from database.entries import (
    save_biotime_entry, fetch_last_entry, fetch_history, fetch_history_limit, build_csv_bytes
)
from database.core import db_enabled

from core.parsing import clamp, parse_float, parse_int, parse_pressure
from core.pro import calc_biotime_pro

from core.assistant.prompts import intro_text as assist_intro_text
from core.assistant.rules import answer_rules as assist_answer_rules


# =========================
# BioTime wizard steps
# =========================
STEP_BT_SLEEP_HOURS = "bt_sleep_hours"
STEP_BT_LATENCY_MIN = "bt_latency_min"
STEP_BT_AWAKENINGS = "bt_awakenings"
STEP_BT_MORNING_FEEL = "bt_morning_feel"
STEP_BT_RHR = "bt_rhr"
STEP_BT_ENERGY = "bt_energy"
STEP_BT_PRESSURE = "bt_pressure"

WIZ_ORDER = [
    STEP_BT_SLEEP_HOURS,
    STEP_BT_LATENCY_MIN,
    STEP_BT_AWAKENINGS,
    STEP_BT_MORNING_FEEL,
    STEP_BT_RHR,
    STEP_BT_ENERGY,
    STEP_BT_PRESSURE,
]


def prompt(step: str):
    if step == STEP_BT_SLEEP_HOURS:
        return "🧬 Новый расчёт\n\n1) Сон (часы)?\nНапример: 7.5"
    if step == STEP_BT_LATENCY_MIN:
        return "2) Засыпание (минут)?\nНапример: 15"
    if step == STEP_BT_AWAKENINGS:
        return "3) Пробуждения (кол-во)?\nНапример: 0"
    if step == STEP_BT_MORNING_FEEL:
        return "4) Самочувствие утром (0–10)?\nНапример: 7"
    if step == STEP_BT_RHR:
        return "5) Пульс покоя (уд/мин)?\nНапример: 58"
    if step == STEP_BT_ENERGY:
        return "6) Энергия (0–10)?\nНапример: 8"
    if step == STEP_BT_PRESSURE:
        return '7) Давление утром SYS/DIA и пульс (например: 120/80 62)\nили напиши: "пропусти"'
    return "…"


def next_step(step: str):
    try:
        i = WIZ_ORDER.index(step)
        return WIZ_ORDER[i + 1] if i + 1 < len(WIZ_ORDER) else None
    except Exception:
        return None


# =========================
# BioTime model (оставляем пока тут, чтобы ничего не сломать)
# позже вынесем в core/
# =========================
def compute_biotime_from_payload(p: dict):
    sleep_h = float(p["sleep_hours"])
    latency = int(p["latency_min"])
    awaken = int(p["awakenings"])
    morning = float(p["morning_feel"])
    rhr = int(p["rhr"])
    energy = float(p["energy"])
    pressure = p.get("pressure")

    sleep_score = clamp((sleep_h / 8.0) * 10.0, 0, 10)

    stress = 0.0
    stress += clamp(latency / 6.0, 0, 5)
    stress += clamp(awaken * 1.5, 0, 5)
    stress = clamp(stress, 0, 10)

    recovery = clamp((morning * 0.55 + energy * 0.45), 0, 10)

    pressure_penalty = 0.0
    risk_penalty = 0.0

    if rhr >= 80:
        pressure_penalty += 1.5
    elif rhr >= 70:
        pressure_penalty += 1.0
    elif rhr <= 50:
        pressure_penalty += 0.3

    if pressure:
        sys = pressure["sys"]
        dia = pressure["dia"]
        if sys >= 140 or dia >= 90:
            pressure_penalty += 2.0
            risk_penalty += 1.0
        elif sys >= 130 or dia >= 85:
            pressure_penalty += 1.0
        elif sys < 100 or dia < 65:
            pressure_penalty += 0.7

    drop_penalty = 0.0
    if sleep_h < 6:
        drop_penalty += 1.0
    if awaken >= 3:
        drop_penalty += 0.5

    biotime = round(
        (sleep_score * 0.6 + recovery * 0.8 - stress * 0.7) + 6.0
        - pressure_penalty - drop_penalty - risk_penalty,
        1
    )
    return clamp(biotime, 0.0, 12.0)


def classify_biotime(biotime: float):
    if biotime < 7:
        mode = "ГЛУБОКОЕ ВОССТАНОВЛЕНИЕ"
        level = "🔴 Низкое"
        status = "ALERT MODE"
        advice = "Сбавь нагрузку. Восстановление приоритет."
        p_train = "Без силовых. Прогулка 20–30 мин. Лёгкая мобильность."
        p_sleep = "Лечь раньше на 1 час. Убрать экран за 60 минут. Тёмная комната."
        p_nutri = "Вода +700 мл. Магний вечером. Лёгкая еда."
    elif biotime <= 11:
        mode = "КОНТРОЛИРУЕМАЯ НАГРУЗКА"
        level = "🟡 Норма"
        status = "NORMAL"
        advice = "Работа без форсирования. Умеренный объём."
        p_train = "Умеренная тренировка 40–60 мин. Без отказа."
        p_sleep = "Обычный режим. Экран убрать за 30–40 мин."
        p_nutri = "Вода +500 мл. Обычное питание."
    else:
        mode = "ФАЗА РОСТА"
        level = "🟢 Оптимум"
        status = "OPTIMAL"
        advice = "Можно нагружать систему. Работай по плану."
        p_train = "Интенсивная работа. Сложные задачи, но без самоубийства."
        p_sleep = "Сохранить режим. Не сдвигать отбой."
        p_nutri = "Полноценное питание. Вода +700 мл."
    return status, level, advice, mode, p_train, p_sleep, p_nutri


def result_block(biotime: float, mode: str, status: str, level: str, advice: str, p_train: str, p_sleep: str, p_nutri: str):
    filled = int(round(clamp(biotime, 0, 12)))
    bar = "▰" * filled + "▱" * (12 - filled)
    return (
        "━━━━━━━━━━━━━━━━━━\n"
        "🧬 BioTime\n\n"
        f"Индекс: {biotime} / 12\n"
        f"{bar}\n\n"
        f"Режим дня: {mode}\n"
        f"Статус: {status}\n"
        f"Зона: {level}\n\n"
        f"Что делать сегодня: {advice}\n\n"
        "Протокол тренировки:\n"
        f"• {p_train}\n\n"
        "Протокол сна:\n"
        f"• {p_sleep}\n\n"
        "Питание/вода:\n"
        f"• {p_nutri}\n"
        "━━━━━━━━━━━━━━━━━━"
    )


# =========================
# UI helpers
# =========================
def ensure_ui(chat_id: int):
    st = get_state(chat_id)
    mid = st.get("ui_message_id")

    if mid:
        ok = edit_message(chat_id, mid, start_text(), main_menu_inline())
        if ok:
            return mid

    new_mid = send_message(chat_id, start_text(), main_menu_inline())
    if new_mid:
        set_state(chat_id, ui_message_id=new_mid, step=None, mode=None, payload=None)
    return new_mid


def core_animation_async(chat_id: int, mid: int, final_text: str):
    def run():
        try:
            steps = [
                ("🧬 Обработка...\n▰▱▱▱▱", after_calc_inline()),
                ("🧠 Анализ...\n▰▰▱▱▱", after_calc_inline()),
                ("🫀 Оценка...\n▰▰▰▱▱", after_calc_inline()),
                ("🔥 Сбор...\n▰▰▰▰▱", after_calc_inline()),
            ]
            for txt, mk in steps:
                edit_message(chat_id, mid, txt, mk)
                time.sleep(0.25)
            edit_message(chat_id, mid, final_text, after_calc_inline())
        except Exception as e:
            print("ANIM ERROR:", repr(e))

    threading.Thread(target=run, daemon=True).start()


def start_biotime_wizard(chat_id: int, ui_mid: int):
    set_state(chat_id, ui_message_id=ui_mid, step=STEP_BT_SLEEP_HOURS, mode=None, payload={})
    edit_message(chat_id, ui_mid, prompt(STEP_BT_SLEEP_HOURS), back_inline())


def profile_text(last_row):
    if not last_row:
        return (
            "🧠 Профиль\n\n"
            "Пока нет данных.\n"
            "Сделай «🧬 Новый расчёт»."
        )
    p = last_row.get("payload_json") or {}
    rhr = p.get("rhr")
    sleep = p.get("sleep_hours")
    return (
        "🧠 Профиль (MVP)\n\n"
        "Сейчас отображаем последние базовые маркеры:\n"
        f"• Сон (последний): {sleep}\n"
        f"• Пульс покоя (последний): {rhr}\n"
    )


def history_block(rows_desc, title: str):
    if not rows_desc:
        return (
            f"📚 История ({title})\n\n"
            "Пока нет записей.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    lines = [f"📚 История ({title})\n"]
    for r in rows_desc:
        ts = r.get("created_at")
        bt = r.get("biotime_value")
        lvl = r.get("level") or "-"
        rec = r.get("recommendation") or "-"
        rec_short = str(rec)
        if len(rec_short) > 60:
            rec_short = rec_short[:57] + "..."
        lines.append(f"• {ts} — {bt}/12 — {lvl} — {rec_short}")
    return "\n".join(lines)


# =========================
# Main entry: handle_update
# =========================
def handle_update(update: dict):
    # =========================
    # CALLBACKS
    # =========================
    if "callback_query" in update:
        cq = update["callback_query"]
        callback_query_id = cq.get("id")
        data = cq.get("data")

        msg = cq.get("message") or {}
        chat_id = (msg.get("chat") or {}).get("id")
        message_id = msg.get("message_id")

        if callback_query_id:
            answer_callback(callback_query_id)

        if not chat_id or not message_id:
            return

        # фиксируем UI message id
        set_state(chat_id, ui_message_id=message_id, step=None, mode=None, payload=None)

        if data == CB_MENU:
            clear_flow(chat_id, keep_ui=True)
            edit_message(chat_id, message_id, start_text(), main_menu_inline())
            return

        if data == CB_INFO:
            edit_message(chat_id, message_id, info_text(), back_inline())
            return

        if data == CB_SETTINGS:
            edit_message(chat_id, message_id, settings_text(), back_inline())
            return

        if data == CB_PROFILE:
            last = fetch_last_entry(chat_id) if db_enabled() else None
            edit_message(chat_id, message_id, profile_text(last), back_inline())
            return

        if data == CB_NEW:
            start_biotime_wizard(chat_id, message_id)
            return

        if data == CB_HISTORY:
            edit_message(chat_id, message_id, "📚 История\n\nВыбери период или экспорт:", history_inline())
            return

        if data == CB_H7:
            rows = fetch_history(chat_id, days=7) if db_enabled() else []
            edit_message(chat_id, message_id, history_block(rows, "7 дней"), history_inline())
            return

        if data == CB_H14:
            rows = fetch_history(chat_id, days=14) if db_enabled() else []
            edit_message(chat_id, message_id, history_block(rows, "14 дней"), history_inline())
            return

        if data == CB_CSV:
            if not db_enabled():
                edit_message(chat_id, message_id, "CSV доступен только при подключённой базе данных (DATABASE_URL).", back_inline())
                return
            rows = fetch_history_limit(chat_id, limit=500)
            b = build_csv_bytes(rows)
            send_document_bytes(chat_id, "aion_history.csv", b, caption="📤 Экспорт AION (CSV)")
            edit_message(chat_id, message_id, "Готово. CSV отправлен в чат.", history_inline())
            return

        if data == CB_ASSIST:
            mid = get_state(chat_id).get("ui_message_id") or ensure_ui(chat_id)
            set_state(chat_id, ui_message_id=mid, step=None, mode="assist", payload={})
            edit_message(chat_id, message_id, assist_intro_text(), back_inline())
            return

        # остальные кнопки (nav/dynamics) подключим чуть позже, когда вынесем блоки
        edit_message(chat_id, message_id, start_text(), main_menu_inline())
        return

    # =========================
    # TEXT
    # =========================
    message = update.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    incoming_message_id = message.get("message_id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return

    if text.startswith("/start") or text == "/menu" or text.lower() in ("start", "старт"):
        clear_flow(chat_id, keep_ui=True)
        ensure_ui(chat_id)
        return

    # /pro — AION PRO
    if text.startswith("/pro"):
        try_delete_user_message(chat_id, incoming_message_id)

        parts = text.split()
        mid = get_state(chat_id).get("ui_message_id") or ensure_ui(chat_id)

        if len(parts) != 7:
            edit_message(chat_id, mid, "⚠️ Неверный формат.\n\n" + pro_hint_text(), back_inline())
            return

        try:
            biotime = calc_biotime_pro(parts[1:])
        except Exception:
            edit_message(chat_id, mid, "⚠️ Ошибка формата.\n\n" + pro_hint_text(), back_inline())
            return

        status, level, advice, mode, p_train, p_sleep, p_nutri = classify_biotime(biotime)
        final_text = result_block(biotime, mode, status, level, advice, p_train, p_sleep, p_nutri)

        save_biotime_entry(chat_id, {"pro": parts[1:]}, biotime, status, level, advice, p_train, p_sleep, p_nutri)

        core_animation_async(chat_id, mid, final_text)
        clear_flow(chat_id, keep_ui=True)
        return

    st = get_state(chat_id)
    step = st.get("step")
    mode = st.get("mode")
    payload = st.get("payload") or {}
    mid = st.get("ui_message_id") or ensure_ui(chat_id)

    # ASSIST MODE
    if mode == "assist" and not step:
        last = fetch_last_entry(chat_id) if db_enabled() else None
        ans = assist_answer_rules(text, last, None)
        edit_message(chat_id, mid, f"💬 Помощник AION\n\nВопрос: {text}\n\n{ans}", back_inline())
        return

    # WIZARD INPUT
    if step:
        try_delete_user_message(chat_id, incoming_message_id)

        try:
            if step == STEP_BT_SLEEP_HOURS:
                v = parse_float(text)
                if v <= 0 or v > 14:
                    raise ValueError()
                payload["sleep_hours"] = v

            elif step == STEP_BT_LATENCY_MIN:
                v = parse_int(text)
                if v < 0 or v > 240:
                    raise ValueError()
                payload["latency_min"] = v

            elif step == STEP_BT_AWAKENINGS:
                v = parse_int(text)
                if v < 0 or v > 20:
                    raise ValueError()
                payload["awakenings"] = v

            elif step == STEP_BT_MORNING_FEEL:
                v = parse_float(text)
                if v < 0 or v > 10:
                    raise ValueError()
                payload["morning_feel"] = v

            elif step == STEP_BT_RHR:
                v = parse_int(text)
                if v < 30 or v > 140:
                    raise ValueError()
                payload["rhr"] = v

            elif step == STEP_BT_ENERGY:
                v = parse_float(text)
                if v < 0 or v > 10:
                    raise ValueError()
                payload["energy"] = v

            elif step == STEP_BT_PRESSURE:
                payload["pressure"] = parse_pressure(text)

            else:
                clear_flow(chat_id, keep_ui=True)
                ensure_ui(chat_id)
                return

        except Exception:
            edit_message(chat_id, mid, "⚠️ Не понял значение.\n\n" + prompt(step), back_inline())
            return

        nxt = next_step(step)
        if nxt:
            set_state(chat_id, ui_message_id=mid, step=nxt, mode=None, payload=payload)
            edit_message(chat_id, mid, prompt(nxt), back_inline())
            return

        # FINALIZE
        try:
            biotime = compute_biotime_from_payload(payload)
            status, level, advice, mode_day, p_train, p_sleep, p_nutri = classify_biotime(biotime)
            final_text = result_block(biotime, mode_day, status, level, advice, p_train, p_sleep, p_nutri)

            save_biotime_entry(chat_id, payload, biotime, status, level, advice, p_train, p_sleep, p_nutri)
            core_animation_async(chat_id, mid, final_text)
        except Exception as e:
            print("FINALIZE ERROR:", repr(e))
            edit_message(chat_id, mid, "⚠️ Ошибка расчёта. Нажми «🧬 Новый расчёт».", after_calc_inline())

        clear_flow(chat_id, keep_ui=True)
        return

    # OTHER TEXT
    ensure_ui(chat_id)