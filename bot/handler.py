import time
import threading

from bot.api import (
    send_message, edit_message, try_delete_user_message,
    answer_callback, send_document_bytes
)

from bot.keyboards import (
    CB_MENU, CB_INFO, CB_SETTINGS, CB_PROFILE, CB_NEW,
    CB_NAV, CB_DYNAMICS, CB_HISTORY,
    CB_H7, CB_H14, CB_CSV, CB_ASSIST,
    main_menu_inline, back_inline, history_inline, after_calc_inline
)

from bot.texts import start_text, info_text, settings_text, pro_hint_text

from database.state import get_state, set_state, clear_flow
from database.entries import (
    save_biotime_entry,
    fetch_last_entry,
    fetch_history,
    fetch_history_limit,
    build_csv_bytes
)
from database.core import db_enabled

from core.parsing import parse_float, parse_int, parse_pressure
from core.pro import calc_biotime_pro
from core.biotime import compute_biotime_from_payload, classify_biotime, result_block

from core.assistant.prompts import intro_text as assist_intro_text
from core.assistant.rules import answer_rules as assist_answer_rules


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


def handle_update(update: dict):

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

        set_state(chat_id, ui_message_id=message_id, step=None, mode=None, payload=None)

        if data == CB_MENU:

            clear_flow(chat_id, keep_ui=True)

            edit_message(chat_id, message_id, start_text(), main_menu_inline())

            return

        if data == CB_NEW:

            start_biotime_wizard(chat_id, message_id)

            return

        edit_message(chat_id, message_id, start_text(), main_menu_inline())

        return

    message = update.get("message") or {}

    chat_id = (message.get("chat") or {}).get("id")

    incoming_message_id = message.get("message_id")

    text = (message.get("text") or "").strip()

    if not chat_id:
        return

    if text.startswith("/start") or text.lower() in ("start", "старт"):

        clear_flow(chat_id, keep_ui=True)

        ensure_ui(chat_id)

        return

    st = get_state(chat_id)

    step = st.get("step")

    payload = st.get("payload") or {}

    mid = st.get("ui_message_id") or ensure_ui(chat_id)

    if step:

        try_delete_user_message(chat_id, incoming_message_id)

        try:

            if step == STEP_BT_SLEEP_HOURS:

                v = parse_float(text)

                payload["sleep_hours"] = v

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

            edit_message(chat_id, mid, "⚠️ Ошибка значения\n\n" + prompt(step), back_inline())

            return

        nxt = next_step(step)

        if nxt:

            set_state(chat_id, ui_message_id=mid, step=nxt, mode=None, payload=payload)

            edit_message(chat_id, mid, prompt(nxt), back_inline())

            return

        biotime = compute_biotime_from_payload(payload)

        status, level, advice, mode_day, p_train, p_sleep, p_nutri = classify_biotime(biotime)

        final_text = result_block(biotime, mode_day, status, level, advice, p_train, p_sleep, p_nutri)

        save_biotime_entry(chat_id, payload, biotime, status, level, advice, p_train, p_sleep, p_nutri)

        core_animation_async(chat_id, mid, final_text)

        clear_flow(chat_id, keep_ui=True)

        return

    ensure_ui(chat_id)