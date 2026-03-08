import time

if text == "/start":

    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "AION\nBiological Upgrade System\n\nИнициализация системы..."
        }
    )

    time.sleep(2)

    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "Анализ биологических параметров..."
        }
    )

    time.sleep(2)

    requests.post(
        f"{TELEGRAM_API_URL}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": "Система готова"
        }
    )

    time.sleep(2)

    keyboard = {
        "inline_keyboard": [
            [
                {
                    "text": "Open AION",
                    "web_app": {
                        "url": "https://aion-bot.onrender.com/app"
                    }
                }
            ]
        ]
    }

    requests.post(
        f"{TELEGRAM_API_URL}/sendPhoto",
        json={
            "chat_id": chat_id,
            "photo": "https://raw.githubusercontent.com/prihodko0501-gif/aion-bot/main/563CC010-50CF-4E76-9C55-A3CEA18351D9.png",
            "reply_markup": keyboard
        }
    )