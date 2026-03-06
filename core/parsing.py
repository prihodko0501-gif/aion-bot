def parse_float(text: str) -> float:
    text = (text or "").strip().replace(",", ".")
    return float(text)


def parse_int(text: str) -> int:
    text = (text or "").strip().replace(",", ".")
    return int(float(text))


def parse_pressure(text: str):
    text = (text or "").strip().lower()

    if text in ("пропусти", "skip", "-", "нет"):
        return {
            "sys": None,
            "dia": None,
            "pulse": None,
            "skipped": True,
        }

    parts = text.split()

    if len(parts) == 1:
        sys_dia = parts[0]
        pulse = None
    elif len(parts) == 2:
        sys_dia, pulse = parts
    else:
        raise ValueError("Неверный формат")

    if "/" not in sys_dia:
        raise ValueError("Неверный формат давления")

    sys_str, dia_str = sys_dia.split("/")

    return {
        "sys": int(sys_str),
        "dia": int(dia_str),
        "pulse": int(pulse) if pulse is not None else None,
        "skipped": False,
    }