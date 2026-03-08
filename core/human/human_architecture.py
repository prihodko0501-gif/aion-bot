def build_human_architecture(payload: dict) -> dict:
    """
    Базовая модель архитектуры организма
    """

    sleep = payload.get("sleep", 0)
    stress = payload.get("stress", 0)
    recovery = payload.get("recovery", 0)

    physiology_score = max(0, sleep - stress)

    nervous_system = max(0, 10 - stress)

    adaptation_capacity = (sleep + recovery) / 2 if (sleep or recovery) else 0

    load_tolerance = max(0, adaptation_capacity - stress)

    recovery_speed = recovery

    wear_profile = stress

    return {
        "physiology": physiology_score,
        "nervous_system": nervous_system,
        "adaptation_capacity": adaptation_capacity,
        "load_tolerance": load_tolerance,
        "recovery_speed": recovery_speed,
        "wear_profile": wear_profile
    }
