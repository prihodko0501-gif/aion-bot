def calculate_physiology(sleep: float, recovery: float, stress: float) -> float:
    """
    Расчёт базовой физиологии организма
    """

    physiology = (sleep + recovery) - stress

    if physiology < 0:
        physiology = 0

    return physiology
