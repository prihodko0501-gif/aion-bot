if text == "/start":
    r = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        json={"chat_id": chat_id, "text": "AION bot запущен ✅"}
    )
    print("sendMessage:", r.status_code, r.text)