# =========================
# КНОПКИ МЕНЮ
# =========================
BTN_NAV = "🧭 Навигация"
BTN_NEW = "🧬 Новый расчёт"
BTN_DYNAMICS = "📊 Динамика"
BTN_HISTORY = "📚 История"
BTN_PROFILE = "🧠 Профиль"
BTN_SETTINGS = "⚙️ Настройки"
BTN_INFO = "ℹ️ О системе"
BTN_ASSIST = "💬 Помощник"

# (на будущее)
BTN_LANG = "🌍 Язык"
BTN_REF = "🎁 Рефералы"

# =========================
# CALLBACKS
# =========================
CB_NAV = "nav"
CB_NEW = "calc_new"
CB_DYNAMICS = "dyn"
CB_HISTORY = "hist"
CB_PROFILE = "profile"
CB_SETTINGS = "settings"
CB_INFO = "info"
CB_ASSIST = "assist"
CB_MENU = "menu"

CB_LANG = "lang"
CB_REF = "ref"

CB_H7 = "hist_7"
CB_H14 = "hist_14"
CB_CSV = "hist_csv"


def main_menu_inline():
    return {
        "inline_keyboard": [
            [{"text": BTN_NAV, "callback_data": CB_NAV}],
            [{"text": BTN_NEW, "callback_data": CB_NEW}],
            [{"text": BTN_DYNAMICS, "callback_data": CB_DYNAMICS}],
            [{"text": BTN_HISTORY, "callback_data": CB_HISTORY}],
            [{"text": BTN_PROFILE, "callback_data": CB_PROFILE}],
            [{"text": BTN_SETTINGS, "callback_data": CB_SETTINGS}],
            [{"text": BTN_INFO, "callback_data": CB_INFO}],
            [{"text": BTN_ASSIST, "callback_data": CB_ASSIST}],
            # будущие:
            # [{"text": BTN_LANG, "callback_data": CB_LANG}],
            # [{"text": BTN_REF, "callback_data": CB_REF}],
        ]
    }


def back_inline():
    return {"inline_keyboard": [[{"text": "⬅️ В меню", "callback_data": CB_MENU}]]}


def history_inline():
    return {
        "inline_keyboard": [
            [{"text": "📅 Показать 7 дней", "callback_data": CB_H7}],
            [{"text": "📅 Показать 14 дней", "callback_data": CB_H14}],
            [{"text": "📤 Экспорт CSV", "callback_data": CB_CSV}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }


def after_calc_inline():
    return {
        "inline_keyboard": [
            [{"text": BTN_NEW, "callback_data": CB_NEW}],
            [{"text": BTN_NAV, "callback_data": CB_NAV}],
            [{"text": BTN_DYNAMICS, "callback_data": CB_DYNAMICS}],
            [{"text": BTN_HISTORY, "callback_data": CB_HISTORY}],
            [{"text": BTN_ASSIST, "callback_data": CB_ASSIST}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }
