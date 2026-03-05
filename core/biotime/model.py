from core.parsing import clamp

def compute_biotime_from_payload(p: dict) -> float:
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

def result_block(biotime: float, mode: str, status: str, level: str, advice: str, p_train: str, p_sleep: str, p_nutri: str) -> str:
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
