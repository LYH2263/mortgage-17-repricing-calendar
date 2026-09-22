import sqlite3
from datetime import datetime, timezone

_COLS = "id,start_month,start_day,end_month,end_day,in_window_rate,out_window_rate,enabled,created_at,updated_at"


def _now():
    return datetime.now(timezone.utc).isoformat()


def list_all(conn):
    return [dict(r) for r in conn.execute(f"SELECT {_COLS} FROM repricing_rules ORDER BY id").fetchall()]


def get(conn, rid):
    row = conn.execute(f"SELECT {_COLS} FROM repricing_rules WHERE id=?", (rid,)).fetchone()
    return dict(row) if row else None


def get_enabled(conn):
    row = conn.execute(f"SELECT {_COLS} FROM repricing_rules WHERE enabled=1 ORDER BY id LIMIT 1").fetchone()
    return dict(row) if row else None


def insert(conn, start_month, start_day, end_month, end_day, in_window_rate, out_window_rate, enabled):
    now = _now()
    cur = conn.execute(
        "INSERT INTO repricing_rules(start_month,start_day,end_month,end_day,in_window_rate,out_window_rate,enabled,created_at,updated_at)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        (start_month, start_day, end_month, end_day, in_window_rate, out_window_rate, int(enabled), now, now))
    conn.commit()
    return int(cur.lastrowid)


def update(conn, rid, start_month, start_day, end_month, end_day, in_window_rate, out_window_rate, enabled):
    conn.execute(
        "UPDATE repricing_rules SET start_month=?,start_day=?,end_month=?,end_day=?,in_window_rate=?,out_window_rate=?,enabled=?,updated_at=?"
        " WHERE id=?",
        (start_month, start_day, end_month, end_day, in_window_rate, out_window_rate, int(enabled), _now(), rid))
    conn.commit()


def set_enabled(conn, rid, enabled):
    conn.execute("UPDATE repricing_rules SET enabled=?,updated_at=? WHERE id=?", (int(enabled), _now(), rid))
    conn.commit()
