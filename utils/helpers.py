from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def now_label() -> str:
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def money(value: float) -> str:
    return f"₹{value:,.2f}"

