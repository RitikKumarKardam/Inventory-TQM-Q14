from datetime import datetime


def now_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value: float) -> str:
    return f"₹{value:,.2f}"
