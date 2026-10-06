from database.db import get_conn


def log_audit(username: str, action: str, entity: str, details: str = "") -> None:
    conn = get_conn()
    conn.execute(
        """
        INSERT INTO audit_log(username,action,entity,details)
        VALUES(?,?,?,?)
        """,
        (username, action, entity, details),
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
    conn.execute(
        """
        INSERT INTO error_log(username,error_code,module,message)
        VALUES(?,?,?,?)
        """,
        (username, error_code, module, message),
    )
    conn.commit()
    conn.close()
