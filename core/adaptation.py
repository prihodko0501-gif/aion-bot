def calculate_adaptation_capacity(sleep: float, stress: float, recovery: float) -> float:
    """
    Расчёт адаптационной ёмкости организма
    """

    base = (sleep + recovery) / 2

    adaptation_capacity = base - (stress * 0.5)

    if adaptation_capacity < 0:
        adaptation_capacity = 0

    return adaptation_capacity
