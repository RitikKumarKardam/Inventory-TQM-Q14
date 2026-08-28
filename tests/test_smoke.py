from app.db import init_db, get_conn

def test_database_schema():
    init_db()
    conn=get_conn()
    names={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    conn.close()
    expected={'users','categories','suppliers','products','stock_movements','audit_log'}
    assert expected.issubset(names)
