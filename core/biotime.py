def calculate_biotime(
    sleep,
    stress,
    recovery,
    pressure_penalty,
    drop_penalty,
    risk_penalty
):

    biotime = round(
        (sleep * 1.2 + recovery * 1.2 - stress)
        - pressure_penalty
        - drop_penalty
        - risk_penalty,
        1
    )

    if biotime < 4:
        level = "🔴 Высокая"
        advice = "Разгрузка / восстановление"

    elif biotime < 8:
        level = "🟠 Средняя"
        advice = "Снизить объём"

    elif biotime <= 11:
        level = "🟡 Норма"
        advice = "Без форсирования"

    else:
        level = "🟢 Оптимум"
        advice = "Работай по плану"

    return biotime, level, advice