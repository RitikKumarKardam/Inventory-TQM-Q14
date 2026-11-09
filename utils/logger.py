from datetime import datetime, timezone, timedelta
from database.db import get_conn

# Indian Standard Time (IST, UTC+05:30)
IST = timezone(timedelta(hours=5, minutes=30))


def get_ist_now_str() -> str:
    """Returns current timestamp in Indian Standard Time (IST, UTC+05:30)."""
    return datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S")


def log_audit(username: str, action: str, entity: str, details: str = "") -> None:
    conn = get_conn()
    now_str = get_ist_now_str()
    conn.execute(
        """
        INSERT INTO audit_log(username, action, entity, details, created_at)
        VALUES(?, ?, ?, ?, ?)
        """,
        (username, action, entity, details, now_str),
    )
    conn.commit()
    conn.close()


def log_error(
    username: str,
    error_code: str,
    module: str,
    message: str,
) -> None:
    conn = get_conn()
    now_str = get_ist_now_str()
    conn.execute(
        """
        INSERT INTO error_log(username, error_code, module, message, created_at)
        VALUES(?, ?, ?, ?, ?)
        """,
        (username, error_code, module, message, now_str),
    )
    conn.commit()
    conn.close()

