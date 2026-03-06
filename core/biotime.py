from core.human.human_architecture import build_human_architecture


def clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def calculate_biotime_pro(
    sleep: float,
    recovery: float,
    stress: float,
    pressure_penalty: float = 0.0,
    drop_penalty: float = 0.0,
    risk_penalty: float = 0.0,
) -> float:
    """
    AION PRO:
    BioTime = round((Sleep*1.2 + Recovery*1.2 - Stress) - PressurePenalty - DropPenalty - RiskPenalty, 1)
    затем clamp 0–12
    """
    value = (
        sleep * 1.2
        + recovery * 1.2
        - stress
        - pressure_penalty
        - drop_penalty
        - risk_penalty
    )
    return clamp(round(value, 1), 0.0, 12.0)


def compute_biotime_from_payload(payload: dict) -> float:
    """
    Основной расчёт BioTime из payload для wizard-режима
    """

    sleep_hours = float(payload.get("sleep_hours", 0))
    latency_min = float(payload.get("latency_min", 0))
    awakenings = float(payload.get("awakenings", 0))
    morning_feel = float(payload.get("morning_feel", 0))
    rhr = float(payload.get("rhr", 0))
    energy = float(payload.get("energy", 0))

    sleep_score = clamp(sleep_hours, 0.0, 10.0)
    recovery_score = clamp((morning_feel + energy) / 2.0, 0.0, 10.0)

    stress_score = (
        latency_min * 0.05
        + awakenings * 0.8
        + max(0.0, (rhr - 60.0)) * 0.05
    )
    stress_score = clamp(stress_score, 0.0, 10.0)

    pressure_penalty = 0.0
    drop_penalty = 0.0
    risk_penalty = 0.0

    pressure = payload.get("pressure")
    if isinstance(pressure, dict):
        sys_val = pressure.get("sys")
        dia_val = pressure.get("dia")

        if isinstance(sys_val, (int, float)) and sys_val >= 140:
            pressure_penalty += 1.0
        if isinstance(dia_val, (int, float)) and dia_val >= 90:
            pressure_penalty += 1.0

    if sleep_hours < 6:
        drop_penalty += 0.5

    human = build_human_architecture(payload)
    recovery_speed = human.get("recovery", {}).get("recovery_speed", recovery_score)

    biotime = calculate_biotime_pro(
        sleep=sleep_score,
        recovery=recovery_speed,
        stress=stress_score,
        pressure_penalty=pressure_penalty,
        drop_penalty=drop_penalty,
        risk_penalty=risk_penalty,
    )

    return biotime


def classify_biotime(biotime: float):
    """
    Возвращает:
    status, level, advice, mode_day, p_train, p_sleep, p_nutri
    """
    if biotime >= 9:
        status = "OPTIMAL"
        level = "🟢 Высокий"
        advice = "Организм в хорошем состоянии. Можно давать рабочую нагрузку."
        mode_day = "Рост / производительность"
        p_train = "Тренировка возможна: силовая или умеренно-интенсивная."
        p_sleep = "Сохраняй режим сна, не сбивай время отбоя."
        p_nutri = "Нормальный рацион, вода, белок, минералы."
    elif biotime >= 6:
        status = "NORMAL"
        level = "🟡 Средний"
        advice = "Состояние рабочее, но без перегруза."
        mode_day = "Поддержание / контроль"
        p_train = "Умеренная тренировка, техника, без отказа."
        p_sleep = "Сделай акцент на восстановление вечером."
        p_nutri = "Чистое питание, контроль воды, без перегруза."
    else:
        status = "LOW"
        level = "🔴 Низкий"
        advice = "Нужен восстановительный режим."
        mode_day = "Восстановление"
        p_train = "Лёгкая активность или отдых."
        p_sleep = "Ранний сон, убрать нагрузку на ЦНС."
        p_nutri = "Вода, электролиты, лёгкое питание, без стресса для ЖКТ."

    return status, level, advice, mode_day, p_train, p_sleep, p_nutri


def result_block(
    biotime: float,
    mode_day: str,
    status: str,
    level: str,
    advice: str,
    p_train: str,
    p_sleep: str,
    p_nutri: str,
) -> str:
    return (
        "🧬 AION BioTime\n\n"
        f"BioTime: {biotime}/12\n"
        f"Режим: {mode_day}\n"
        f"Статус: {status}\n"
        f"Уровень: {level}\n\n"
        f"Что делать: {advice}\n\n"
        f"Тренировка: {p_train}\n"
        f"Сон: {p_sleep}\n"
        f"Питание: {p_nutri}"
    )


def calculate_aion_state(payload: dict) -> dict:
    """
    Полный расчёт состояния организма AION
    """
    human = build_human_architecture(payload)

    biotime = compute_biotime_from_payload(payload)

    status, level, advice, mode_day, p_train, p_sleep, p_nutri = classify_biotime(biotime)

    return {
        "biotime": biotime,
        "human_model": human,
        "status": status,
        "level": level,
        "advice": advice,
        "mode_day": mode_day,
        "protocols": {
            "training": p_train,
            "sleep": p_sleep,
            "nutrition": p_nutri,
        },
    }