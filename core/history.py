def history_block(rows_desc, title: str) -> str:
    if not rows_desc:
        return (
            f"📚 История ({title})\n\n"
            "Пока нет записей.\n"
            "Сделай «🧬 Новый расчёт»."
        )

    lines = [f"📚 История ({title})\n"]
    for r in rows_desc:
        ts = r.get("created_at")
        bt = r.get("biotime_value")
        lvl = r.get("level") or "-"
        rec = r.get("recommendation") or "-"
        rec_short = str(rec)
        if len(rec_short) > 60:
            rec_short = rec_short[:57] + "..."
        lines.append(f"• {ts} — {bt}/12 — {lvl} — {rec_short}")
    return "\n".join(lines)
