def build_head(last_entry: dict | None, nav: dict | None = None) -> str:
    """
    last_entry: dict с полями (biotime_value, level, recommendation, payload_json)
    nav: dict от navigation.calc_nav_metrics (опционально)
    """
    if not last_entry:
        return ""

    bt = last_entry.get("biotime_value")
    lvl = last_entry.get("level") or "-"
    rec = last_entry.get("recommendation") or "-"

    head = (
        "Текущее состояние:\n"
        f"• BioTime: {bt}/12\n"
        f"• Зона: {lvl}\n"
        f"• Что делать сегодня: {rec}\n"
    )
    if nav:
        head += f"• Индекс AION 1: {nav.get('index_1000')}/1000, риск 30 дней: {nav.get('risk')}%\n"
    return head


def answer_rules(question: str, last_entry: dict | None, nav: dict | None = None) -> str:
    """
    Простой rule-based помощник.
    """
    q = (question or "").strip()
    if not q:
        return "Напиши вопрос текстом."

    if not last_entry:
        return (
            "Сейчас нет данных по твоему состоянию.\n"
            "Сделай «🧬 Новый расчёт», и я буду отвечать точнее."
        )

    head = build_head(last_entry, nav)
    ql = q.lower()

    bt = float(last_entry.get("biotime_value") or 0)

    # тренировки
    if any(k in ql for k in ("трен", "зал", "нагруз", "силов", "кардио")):
        if bt < 7:
            return head + "\nПо тренировке: сегодня восстановление (без тяжёлых силовых)."
        if bt <= 11:
            return head + "\nПо тренировке: умеренно, без отказа и без добивания."
        return head + "\nПо тренировке: можно интенсивнее, но держи технику и сон."

    # сон
    if any(k in ql for k in ("сон", "спат", "отбой", "засып")):
        return head + "\nПо сну: сегодня приоритет — стабильный отбой + убрать экран минимум за 30–60 минут."

    # питание/вода
    if any(k in ql for k in ("пит", "еда", "вода", "углев", "белок")):
        return head + "\nПо питанию/воде: добавь воду (500–700 мл), вечером еда без перегруза ЖКТ."

    # стресс/нервы
    if any(k in ql for k in ("стресс", "нерв", "тревог", "кортиз")):
        return head + "\nПо стрессу: сегодня снизь стимулы, сделай прогулку 20–30 мин и дыхание 5–7 мин."

    return head + "\nОтвет: уточни цель (тренировка/сон/питание/стресс), и я дам протокол точнее."
