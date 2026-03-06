from urllib.parse import quote


CB_NAV = "nav"
CB_NEW = "new_calc"
CB_DYN = "dynamics"
CB_HIS = "history"
CB_PROFILE = "profile"
CB_SETTINGS = "settings"
CB_ABOUT = "about"
CB_ASSIST = "assist"
CB_MENU = "menu"
CB_BACK = "back"


def main_menu(webapp_url: str | None = None):
    rows = [
        [{"text": "🧭 Навигация", "callback_data": CB_NAV}],
        [{"text": "🧬 Новый расчёт", "callback_data": CB_NEW}],
        [{"text": "📊 Динамика", "callback_data": CB_DYN}],
        [{"text": "📚 История", "callback_data": CB_HIS}],
        [{"text": "🧠 Профиль", "callback_data": CB_PROFILE}],
        [{"text": "⚙️ Настройки", "callback_data": CB_SETTINGS}],
        [{"text": "ℹ️ О системе", "callback_data": CB_ABOUT}],
        [{"text": "💬 Помощник", "callback_data": CB_ASSIST}],
    ]

    if webapp_url:
        rows.append([{"text": "📱 Mini App", "web_app": {"url": webapp_url}}])

    return {"inline_keyboard": rows}


def back_to_menu():
    return {
        "inline_keyboard": [
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}]
        ]
    }


def back_and_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "⬅️ Назад", "callback_data": CB_BACK},
                {"text": "🏠 Меню", "callback_data": CB_MENU},
            ]
        ]
    }