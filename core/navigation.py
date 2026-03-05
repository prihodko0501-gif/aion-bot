def clamp(x, a, b):
    return max(a, min(b, x))

def avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None

def calc_nav_metrics(series: list[float]) -> dict | None:
    """
    series — список BioTime значений по времени (по возрастанию).
    Возвращает: index_1000, vector, buffer_days, accum_days, risk, wear_rate, stability
    """
    if not series:
        return None

    current = series[-1]
    index_1000 = int(round(clamp(current / 12.0, 0, 1) * 1000))

    last7 = series[-7:] if len(series) >= 7 else series
    last30 = series[-30:] if len(series) >= 30 else series
    a7 = avg(last7)
    a30 = avg(last30)

    delta = (a7 - a30) if (a7 is not None and a30 is not None) else 0.0
    vector = int(round(delta * 20))

    # накопление перегруза (сколько дней подряд 7д < 30д)
    accum_days = 0
    for k in range(1, min(len(series), 30) + 1):
        sub = series[-k:]
        sub7 = sub[-7:] if len(sub) >= 7 else sub
        sub30 = sub[-30:] if len(sub) >= 30 else sub
        s7 = avg(sub7)
        s30 = avg(sub30)
        if s7 is not None and s30 is not None and (s7 < s30):
            accum_days += 1
        else:
            break

    buffer_days = int(round(clamp((a7 - 7.0), 0, 5))) if a7 is not None else 0

    base = 50.0
    if a7 is not None:
        base += (7.5 - a7) * 8.0
    base += (-delta) * 25.0
    risk = int(round(clamp(base, 5, 95)))

    wear_rate = round(clamp((-delta) * 30.0, 0.0, 12.0), 2)
    stability = int(round(clamp((a7 / 12.0) * 100.0, 0, 100))) if a7 is not None else 0

    if index_1000 < 420:
        regime = "ВОССТАНОВЛЕНИЕ"
    elif index_1000 < 780:
        regime = "КОНТРОЛИРУЕМАЯ НАГРУЗКА"
    else:
        regime = "РОСТ"

    return {
        "index_1000": index_1000,
        "vector": vector,
        "accum_days": accum_days,
        "buffer_days": buffer_days,
        "risk": risk,
        "regime": regime,
        "current_biotime": round(current, 1),
        "wear_rate": wear_rate,
        "stability": stability,
    }
