def parse_float(text: str) -> float:
    text = text.replace(",", ".").strip()
    return float(text)


def parse_int(text: str) -> int:
    return int(text.strip())


def parse_pressure(text: str):
    text = text.lower().strip()

    if text in ("skip", "пропусти", "пропустить"):
        return None

    parts = text.split()

    if len(parts) == 1:
        sys_dia = parts[0]
        pulse = None
    else:
        sys_dia, pulse = parts

    sys, dia = sys_dia.split("/")

    return {
        "sys": int(sys),
        "dia": int(dia),
        "pulse": int(pulse) if pulse else None
    }
