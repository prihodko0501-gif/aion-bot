def main_menu():
    return {
        "inline_keyboard": [
            [
                {"text": "🧬 Новый расчёт", "callback_data": "new_calc"},
                {"text": "🧭 Навигация", "callback_data": "nav"}
            ],
            [
                {"text": "📊 Динамика", "callback_data": "dynamics"},
                {"text": "📚 История", "callback_data": "history"}
            ],
            [
                {"text": "🧠 Профиль", "callback_data": "profile"},
                {"text": "⚙️ Настройки", "callback_data": "settings"}
            ],
            [
                {"text": "ℹ️ О системе", "callback_data": "about"}
            ],
            [
                {
                    "text": "📱 Mini App",
                    "web_app": {"url": "https://aion-bot.onrender.com"}
                }
            ]
        ]
    }


def back_to_menu():
    return {
        "inline_keyboard": [
            [{"text": "⬅️ Назад в меню", "callback_data": "menu"}]
        ]
    }