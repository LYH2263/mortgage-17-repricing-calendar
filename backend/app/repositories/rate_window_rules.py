from datetime import datetime, timezone


def _row(r):
    d = dict(r)
    d["enabled"] = bool(d.get("enabled"))
    return d


def list_all(conn):
    rows = conn.execute(
        "SELECT * FROM rate_window_rules ORDER BY id DESC").fetchall()
    return [_row(r) for r in rows]


def get(conn, rid):
    r = conn.execute(
        "SELECT * FROM rate_window_rules WHERE id=?", (rid,)).fetchone()
    return _row(r) if r else None


def active(conn):
    r = conn.execute(
        "SELECT * FROM rate_window_rules WHERE enabled=1 ORDER BY id LIMIT 1").fetchone()
    return _row(r) if r else None


def insert(conn, data, commit=True):
    now = datetime.now(timezone.utc).isoformat()
    cur = conn.execute(
        "INSERT INTO rate_window_rules"
        "(start_month,start_day,end_month,end_day,in_rate,out_rate,enabled,created_at)"
        " VALUES (?,?,?,?,?,?,?,?)",
        (data["start_month"], data["start_day"], data["end_month"], data["end_day"],
         data["in_rate"], data["out_rate"], 1 if data["enabled"] else 0, now))
    if commit:
        conn.commit()
    return int(cur.lastrowid)


def update(conn, rid, data):
    cur = conn.execute(
        "UPDATE rate_window_rules SET start_month=?,start_day=?,end_month=?,end_day=?,"
        "in_rate=?,out_rate=?,enabled=? WHERE id=?",
        (data["start_month"], data["start_day"], data["end_month"], data["end_day"],
         data["in_rate"], data["out_rate"], 1 if data["enabled"] else 0, rid))
    conn.commit()
    return cur.rowcount > 0


def disable(conn, rid):
    cur = conn.execute(
        "UPDATE rate_window_rules SET enabled=0 WHERE id=?", (rid,))
    conn.commit()
    return cur.rowcount > 0
