def compute_biotime_from_payload(payload: dict) -> float:
    sleep = payload.get("sleep_hours", 0)
    latency = payload.get("latency_min", 0)
    awaken = payload.get("awakenings", 0)
    feel = payload.get("morning_feel", 0)
    rhr = payload.get("rhr", 60)
    energy = payload.get("energy", 0)

    score = 0

    score += sleep * 0.8
    score -= latency * 0.05
    score -= awaken * 0.5
    score += feel * 0.8
    score += energy * 0.7
    score -= max(0, rhr - 55) * 0.05

    return round(max(0, min(12, score)), 1)


def classify_biotime(biotime: float):
    if biotime >= 9:
        status = "Оптимальное состояние"
        level = "🟢 высокий"
        advice = "Можно тренироваться интенсивно"
        mode_day = "Активный день"

    elif biotime >= 6:
        status = "Нормальное состояние"
        level = "🟡 средний"
        advice = "Поддерживающая нагрузка"
        mode_day = "Рабочий режим"

    else:
        status = "Перегрузка"
        level = "🔴 низкий"
        advice = "Лучше восстановление"
        mode_day = "Восстановительный режим"

    protocol_training = "Лёгкая тренировка"
    protocol_sleep = "Лечь раньше"
    protocol_nutrition = "Повысить белок"

    return (
        status,
        level,
        advice,
        mode_day,
        protocol_training,
        protocol_sleep,
        protocol_nutrition,
    )


def result_block(
    biotime,
    mode_day,
    status,
    level,
    advice,
    p_train,
    p_sleep,
    p_nutri,
):
    text = (
        f"🧬 BioTime: {biotime}\n\n"
        f"📊 Статус: {status}\n"
        f"📈 Уровень: {level}\n\n"
        f"📅 Режим дня: {mode_day}\n\n"
        f"🏋️ Тренировка: {p_train}\n"
        f"😴 Сон: {p_sleep}\n"
        f"🥗 Питание: {p_nutri}\n\n"
        f"💡 Рекомендация: {advice}"
    )

    return text