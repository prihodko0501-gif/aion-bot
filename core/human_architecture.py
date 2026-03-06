def build_human_architecture(payload: dict) -> dict:
    """
    Базовая модель архитектуры человека для системы AION
    """

    sleep = payload.get("sleep", 0)
    stress = payload.get("stress", 0)
    recovery = payload.get("recovery", 0)

    # Простая модель физиологии
    physiology_score = max(0, sleep - stress)

    # Нервная система
    nervous_system = max(0, 10 - stress)

    # Адаптационная ёмкость
    adaptation_capacity = (sleep + recovery) / 2 if (sleep or recovery) else 0

    # Толерантность к нагрузке
    load_tolerance = max(0, adaptation_capacity - stress)

    # Скорость восстановления
    recovery_speed = recovery

    # Профиль износа
    wear_profile = stress

    return {
        "physiology": physiology_score,
        "nervous_system": nervous_system,
        "adaptation_capacity": adaptation_capacity,
        "load_tolerance": load_tolerance,
        "recovery_speed": recovery_speed,
        "wear_profile": wear_profile
    }
