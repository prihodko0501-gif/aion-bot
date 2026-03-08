import os
import time
import threading

from bot.api import (
    send_message,
    edit_message,
    answer_callback_query,
    remove_reply_keyboard,
)
from bot.keyboards import (
    main_menu,
    back_to_menu,
    history_menu,
    CB_NAV,
    CB_NEW,
    CB_DYN,
    CB_HIS,
    CB_PROFILE,
    CB_SETTINGS,
    CB_ABOUT,
    CB_ASSIST,
    CB_MENU,
    CB_H7,
    CB_H14,
)
from bot import texts
from database.state import get_state, set_state, clear_state
from database.entries import (
    save_biotime_entry,
    fetch_history,
    fetch_history_limit,
    fetch_last_entry,
)
from core.parsing import parse_float, parse_int, parse_pressure
from core.biotime import (
    compute_biotime_from_payload,
    classify_biotime,
    result_block,
)

WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip() or None

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
    return "..."


def next_step(step: str):
    try:
        i = WIZ_ORDER.index(step)
        if i + 1 < len(WIZ_ORDER):
            return WIZ_ORDER[i + 1]
        return None
    except Exception:
        return None


def safe_edit(chat_id, message_id, text, reply_markup=None):
    result = edit_message(chat_id, message_id, text, reply_markup=reply_markup)
    if result.get("ok"):
        return True

    sent = send_message(chat_id, text, reply_markup=reply_markup)
    if sent.get("ok"):
        msg = sent.get("result", {})
        set_state(chat_id, ui_message_id=msg.get("message_id"))
        return True

    return False


def show_main_menu(chat_id, message_id=None):
    text = (
        "AION — система управления скоростью "
        "биологического износа на основании "
        "анализа твоей физиологии.\n\n"
        "Выбери действие:"
    )
    markup = main_menu(WEBAPP_URL)

    if message_id:
        result = edit_message(chat_id, message_id, text, reply_markup=markup)
        if result.get("ok"):
            set_state(chat_id, ui_message_id=message_id, step=None, payload={})
            return

    sent = send_message(chat_id, text, reply_markup=markup)
    if sent.get("ok"):
        msg = sent.get("result", {})
        set_state(chat_id, ui_message_id=msg.get("message_id"), step=None, payload={})


def after_calc_menu():
    return {
        "inline_keyboard": [
            [{"text": "🧬 Новый расчёт", "callback_data": CB_NEW}],
            [{"text": "🧭 Навигация", "callback_data": CB_NAV}],
            [{"text": "📊 Динамика", "callback_data": CB_DYN}],
            [{"text": "📚 История", "callback_data": CB_HIS}],
            [{"text": "💬 Помощник", "callback_data": CB_ASSIST}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }


def core_animation_async(chat_id: int, message_id: int, final_text: str):
    def run():
        try:
            steps = [
                "🧬 Обработка...\n▰▱▱▱▱",
                "🧠 Анализ...\n▰▰▱▱▱",
                "🫀 Оценка...\n▰▰▰▱▱",
                "🔥 Сбор результата...\n▰▰▰▰▱",
                "⚡ Финализация...\n▰▰▰▰▰",
            ]

            for txt in steps:
                edit_message(chat_id, message_id, txt, reply_markup=after_calc_menu())
                time.sleep(0.35)

            edit_message(chat_id, message_id, final_text, reply_markup=after_calc_menu())

        except Exception as e:
            print("ANIMATION ERROR:", repr(e))

    threading.Thread(target=run, daemon=True).start()


def render_profile(chat_id, message_id):
    last = fetch_last_entry(chat_id)

    if not last:
        text = "🧠 Профиль\n\nПока нет данных.\nСделай новый расчёт."
    else:
        created_at, biotime = last
        text = (
            "🧠 Профиль\n\n"
            f"Последний BioTime: {round(float(biotime), 1)}\n"
            f"Последняя запись: {created_at}"
        )

    safe_edit(chat_id, message_id, text, back_to_menu())


def render_history(chat_id, message_id, days=7):
    rows = fetch_history(chat_id, days=days)

    if not rows:
        text = f"📚 История за {days} дней\n\nПока записей нет."
        safe_edit(chat_id, message_id, text, history_menu())
        return

    lines = [f"📚 История за {days} дней\n"]
    for created_at, biotime in rows[:15]:
        lines.append(f"• {created_at:%d.%m %H:%M} — BioTime {round(float(biotime), 1)}")

    safe_edit(chat_id, message_id, "\n".join(lines), history_menu())


def render_navigation(chat_id, message_id):
    rows = fetch_history_limit(chat_id, limit=30)

    if not rows:
        text = "🧭 Навигация\n\nПока нет данных для навигации."
        safe_edit(chat_id, message_id, text, back_to_menu())
        return

    values = [float(row[1]) for row in rows]
    current = values[0]
    avg = sum(values) / len(values)
    trend = current - avg

    if trend > 0.3:
        vector = "↗️ Улучшение"
    elif trend < -0.3:
        vector = "↘️ Снижение"
    else:
        vector = "➡️ Стабильно"

    text = (
        "🧭 Навигация AION\n\n"
        f"Текущий BioTime: {round(current, 1)}\n"
        f"Средний BioTime: {round(avg, 1)}\n"
        f"Вектор: {vector}\n"
        f"Записей учтено: {len(values)}"
    )

    safe_edit(chat_id, message_id, text, back_to_menu())


def render_dynamics(chat_id, message_id):
    rows = fetch_history_limit(chat_id, limit=30)

    if not rows:
        text = "📊 Динамика\n\nПока нет данных."
        safe_edit(chat_id, message_id, text, back_to_menu())
        return

    values = [float(row[1]) for row in rows]
    current = values[0]
    oldest = values[-1]
    delta = round(current - oldest, 1)

    text = (
        "📊 Динамика\n\n"
        f"Текущий BioTime: {round(current, 1)}\n"
        f"Первый в выборке: {round(oldest, 1)}\n"
        f"Изменение: {delta}"
    )

    safe_edit(chat_id, message_id, text, back_to_menu())


def render_assist(chat_id, message_id):
    text = "💬 Помощник AION\n\nБазовый режим."
    safe_edit(chat_id, message_id, text, back_to_menu())


def handle_update(update):
    try:
        if "callback_query" in update:
            handle_callback(update["callback_query"])
            return

        if "message" in update:
            handle_message(update["message"])
            return

        print("UNKNOWN UPDATE:", update)

    except Exception as e:
        print("HANDLE_UPDATE ERROR:", repr(e))


def handle_message(message):
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return

    if text == "/start" or text.lower() in ("start", "старт"):
        clear_state(chat_id)
        remove_reply_keyboard(chat_id)
        show_main_menu(chat_id)
        return

    legacy_buttons = {
        "🧬 biotime",
        "biotime",
        "sleep",
        "cns",
        "recovery",
        "pressure",
        "info",
        "🛌 sleep",
        "🧠 cns",
        "🔥 recovery",
        "❤️ pressure",
        "ℹ️ info",
    }

    if text.lower() in legacy_buttons:
        remove_reply_keyboard(chat_id)
        show_main_menu(chat_id)
        return

    state = get_state(chat_id)
    step = state.get("step")
    message_id = state.get("ui_message_id")

    if not step:
        show_main_menu(chat_id)
        return

    payload = state.get("payload", {})

    try:
        if step == STEP_BT_SLEEP_HOURS:
            payload["sleep_hours"] = parse_float(text)
        elif step == STEP_BT_LATENCY_MIN:
            payload["latency_min"] = parse_int(text)
        elif step == STEP_BT_AWAKENINGS:
            payload["awakenings"] = parse_int(text)
        elif step == STEP_BT_MORNING_FEEL:
            payload["morning_feel"] = parse_float(text)
        elif step == STEP_BT_RHR:
            payload["rhr"] = parse_int(text)
        elif step == STEP_BT_ENERGY:
            payload["energy"] = parse_float(text)
        elif step == STEP_BT_PRESSURE:
            payload["pressure"] = parse_pressure(text)
    except Exception:
        safe_edit(chat_id, message_id, "⚠️ Ошибка значения\n\n" + prompt(step), back_to_menu())
        return

    nxt = next_step(step)

    if nxt:
        set_state(chat_id, step=nxt, payload=payload)
        safe_edit(chat_id, message_id, prompt(nxt), back_to_menu())
        return

    try:
        biotime = compute_biotime_from_payload(payload)
        status, level, advice, mode_day, p_train, p_sleep, p_nutri = classify_biotime(biotime)

        final_text = result_block(
            biotime,
            mode_day,
            status,
            level,
            advice,
            p_train,
            p_sleep,
            p_nutri,
        )
    except Exception as e:
        print("BIOTIME ERROR:", repr(e))
        safe_edit(chat_id, message_id, "⚠️ Ошибка расчёта. Попробуй ещё раз.", back_to_menu())
        clear_state(chat_id)
        return

    try:
        save_biotime_entry(
            chat_id,
            payload,
            biotime,
            status,
            level,
            advice,
            p_train,
            p_sleep,
            p_nutri,
        )
    except Exception as e:
        print("SAVE ENTRY ERROR:", repr(e))

    core_animation_async(chat_id, message_id, final_text)
    clear_state(chat_id)


def handle_callback(callback):
    callback_id = callback["id"]
    data = callback.get("data", "")
    msg = callback.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")

    answer_callback_query(callback_id)

    if not chat_id or not message_id:
        return

    if data == CB_MENU:
        clear_state(chat_id)
        show_main_menu(chat_id, message_id)
        return

    if data == CB_NAV:
        render_navigation(chat_id, message_id)
        return

    if data == CB_NEW:
        set_state(chat_id, ui_message_id=message_id, step=STEP_BT_SLEEP_HOURS, payload={})
        safe_edit(chat_id, message_id, prompt(STEP_BT_SLEEP_HOURS), back_to_menu())
        return

    if data == CB_DYN:
        render_dynamics(chat_id, message_id)
        return

    if data == CB_HIS:
        render_history(chat_id, message_id, days=7)
        return

    if data == CB_H7:
        render_history(chat_id, message_id, days=7)
        return

    if data == CB_H14:
        render_history(chat_id, message_id, days=14)
        return

    if data == CB_PROFILE:
        render_profile(chat_id, message_id)
        return

    if data == CB_SETTINGS:
        safe_edit(chat_id, message_id, "⚙️ Настройки", back_to_menu())
        return

    if data == CB_ABOUT:
        safe_edit(chat_id, message_id, "ℹ️ О системе", back_to_menu())
        return

    if data == CB_ASSIST:
        render_assist(chat_id, message_id)
        return

    show_main_menu(chat_id, message_id)