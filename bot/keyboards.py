CB_NAV = "nav"
CB_NEW = "new_calc"
CB_HIS = "history"
CB_ASSIST = "assist"
CB_MENU = "menu"

CB_H7 = "hist_7"
CB_H14 = "hist_14"


def main_menu(webapp_url=None):
    rows = [
        [{"text": "🧬 Новый расчёт", "callback_data": CB_NEW}],
        [{"text": "🧭 Навигация", "callback_data": CB_NAV}],
        [{"text": "📚 История", "callback_data": CB_HIS}],
        [{"text": "💬 Помощник", "callback_data": CB_ASSIST}],
    ]

    if webapp_url:
        rows.append([
            {
                "text": "📱 Mini App",
                "web_app": {"url": webapp_url}
            }
        ])

    return {"inline_keyboard": rows}


def back_to_menu():
    return {
        "inline_keyboard": [
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}]
        ]
    }


def history_menu():
    return {
        "inline_keyboard": [
            [{"text": "📅 7 дней", "callback_data": CB_H7}],
            [{"text": "📅 14 дней", "callback_data": CB_H14}],
            [{"text": "⬅️ В меню", "callback_data": CB_MENU}],
        ]
    }