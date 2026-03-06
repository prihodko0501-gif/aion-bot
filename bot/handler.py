import os

from bot.api import send_message, edit_message, answer_callback_query
from bot.keyboards import (
    main_menu,
    back_to_menu,
    CB_NAV,
    CB_NEW,
    CB_DYN,
    CB_HIS,
    CB_PROFILE,
    CB_SETTINGS,
    CB_ABOUT,
    CB_ASSIST,
    CB_MENU,
)
from bot import texts
from database.state import get_state, set_state, clear_state


WEBAPP_URL = os.getenv("WEBAPP_URL", "").strip() or None


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
        print("HANDLE_UPDATE ERROR:", e)


def handle_message(message):
    chat_id = message.get("chat", {}).get("id")
    text = (message.get("text") or "").strip()

    if not chat_id:
        return

    if text == "/start":
        clear_state(chat_id)
        show_main_menu(chat_id)
        return

    state = get_state(chat_id)
    step = state.get("step")

    if step == "new_calc_sleep":
        # пока заглушка, позже сюда вольём wizard
        show_screen(chat_id, texts.NEW_CALC_TEXT, save_as_main=True)
        return

    show_main_menu(chat_id)


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
        edit_or_send_main_menu(chat_id, message_id)
        return

    if data == CB_NAV:
        edit_screen(chat_id, message_id, texts.NAV_TEXT)
        return

    if data == CB_NEW:
        set_state(chat_id, step="new_calc_sleep")
        edit_screen(chat_id, message_id, texts.NEW_CALC_TEXT)
        return

    if data == CB_DYN:
        edit_screen(chat_id, message_id, texts.DYNAMICS_TEXT)
        return

    if data == CB_HIS:
        edit_screen(chat_id, message_id, texts.HISTORY_TEXT)
        return

    if data == CB_PROFILE:
        edit_screen(chat_id, message_id, texts.PROFILE_TEXT)
        return

    if data == CB_SETTINGS:
        edit_screen(chat_id, message_id, texts.SETTINGS_TEXT)
        return

    if data == CB_ABOUT:
        edit_screen(chat_id, message_id, texts.ABOUT_TEXT)
        return

    if data == CB_ASSIST:
        edit_screen(chat_id, message_id, texts.ASSIST_TEXT)
        return

    edit_or_send_main_menu(chat_id, message_id)


def show_main_menu(chat_id):
    result = send_message(
        chat_id,
        texts.WELCOME_TEXT,
        reply_markup=main_menu(WEBAPP_URL)
    )
    if result.get("ok"):
        msg = result.get("result", {})
        set_state(chat_id, ui_message_id=msg.get("message_id"), step=None)


def edit_or_send_main_menu(chat_id, message_id):
    result = edit_message(
        chat_id,
        message_id,
        texts.WELCOME_TEXT,
        reply_markup=main_menu(WEBAPP_URL)
    )

    if not result.get("ok"):
        show_main_menu(chat_id)


def edit_screen(chat_id, message_id, text):
    result = edit_message(
        chat_id,
        message_id,
        text,
        reply_markup=back_to_menu()
    )
    if not result.get("ok"):
        sent = send_message(chat_id, text, reply_markup=back_to_menu())
        if sent.get("ok"):
            msg = sent.get("result", {})
            set_state(chat_id, ui_message_id=msg.get("message_id"))


def show_screen(chat_id, text, save_as_main=False):
    result = send_message(chat_id, text, reply_markup=back_to_menu())
    if save_as_main and result.get("ok"):
        msg = result.get("result", {})
        set_state(chat_id, ui_message_id=msg.get("message_id"))