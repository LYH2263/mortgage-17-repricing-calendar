import json
import os
import tempfile

os.environ["DATA_DIR"] = tempfile.mkdtemp(prefix="mortgage-test-")

import pytest
from fastapi import HTTPException
from app import seed
from app.db import connect
from app.engines.repricing import in_window, valid_month_day
from app.repositories import repricing_rules
from app.routers.repricing import create_rule, update_rule
from app.schemas.repricing import RepricingRuleIn
from app.services.mortgage_service import MortgageService

seed.init_db()


@pytest.fixture(autouse=True)
def clean_tables():
    conn = connect()
    conn.execute("DELETE FROM repricing_rules")
    conn.execute("DELETE FROM calc_runs")
    conn.commit()
    conn.close()
    yield


def _add_rule(enabled=1, **kw):
    args = dict(start_month=11, start_day=1, end_month=2, end_day=28,
                in_window_rate=3.10, out_window_rate=3.60, enabled=enabled)
    args.update(kw)
    conn = connect()
    rid = repricing_rules.insert(conn, *[args[k] for k in
        ("start_month", "start_day", "end_month", "end_day", "in_window_rate", "out_window_rate", "enabled")])
    conn.close()
    return rid


# ---- 窗判定 ----

def test_window_same_year():
    assert in_window(3, 1, 6, 30, 4, 15)
    assert not in_window(3, 1, 6, 30, 7, 1)


def test_window_cross_year():
    assert in_window(11, 1, 2, 28, 12, 25)
    assert in_window(11, 1, 2, 28, 1, 10)
    assert not in_window(11, 1, 2, 28, 5, 1)


def test_window_boundaries_inclusive():
    assert in_window(11, 1, 2, 28, 11, 1)
    assert in_window(11, 1, 2, 28, 2, 28)
    assert not in_window(11, 1, 2, 28, 10, 31)
    assert not in_window(11, 1, 2, 28, 3, 1)


def test_valid_month_day():
    assert valid_month_day(2, 29)
    assert not valid_month_day(2, 30)
    assert not valid_month_day(4, 31)
    assert not valid_month_day(13, 1)


# ---- 启用冲突 ----

def test_conflict_create_names_both_rules():
    rid = _add_rule(enabled=1)
    body = RepricingRuleIn(start_month=5, start_day=1, end_month=8, end_day=31,
                           in_window_rate=3.0, out_window_rate=3.5, enabled=True)
    with pytest.raises(HTTPException) as e:
        create_rule(body)
    assert e.value.status_code == 409
    assert f"规则#{rid}" in e.value.detail and "新规则" in e.value.detail


def test_conflict_update_names_both_rules():
    first = _add_rule(enabled=1)
    second = _add_rule(enabled=0)
    body = RepricingRuleIn(start_month=5, start_day=1, end_month=8, end_day=31,
                           in_window_rate=3.0, out_window_rate=3.5, enabled=True)
    with pytest.raises(HTTPException) as e:
        update_rule(second, body)
    assert e.value.status_code == 409
    assert f"规则#{first}" in e.value.detail and f"规则#{second}" in e.value.detail


def test_disabled_rules_coexist():
    _add_rule(enabled=0)
    _add_rule(enabled=0)
    conn = connect()
    assert len(repricing_rules.list_all(conn)) == 2
    conn.close()


# ---- 测算定价 ----

def test_schedule_hit_window_uses_in_rate():
    _add_rule(enabled=1)
    with MortgageService() as s:
        out = s.schedule(1_000_000, 9.99, 360, None, False, start_month=12, start_day=1)
    assert out["window_hit"] is True
    assert out["annual_rate_used"] == 3.10
    assert out["monthly_payment"] == 4270.16  # 等额本息 @3.10


def test_schedule_outside_window_uses_out_rate():
    _add_rule(enabled=1)
    with MortgageService() as s:
        out = s.schedule(1_000_000, 9.99, 360, None, False, start_month=6, start_day=15)
    assert out["window_hit"] is False
    assert out["annual_rate_used"] == 3.60
    assert out["monthly_payment"] == 4546.45  # 等额本息 @3.60


def test_schedule_no_start_month_day_falls_back():
    _add_rule(enabled=1)
    with MortgageService() as s:
        out = s.schedule(1_000_000, 3.5, 360, None, False)
    assert out["window_hit"] is None
    assert out["annual_rate_used"] == 3.5
    assert out["monthly_payment"] == 4490.45


def test_schedule_disabled_rule_falls_back():
    _add_rule(enabled=0)
    with MortgageService() as s:
        out = s.schedule(1_000_000, 3.5, 360, None, False, start_month=12, start_day=1)
    assert out["window_hit"] is None
    assert out["annual_rate_used"] == 3.5
    assert out["monthly_payment"] == 4490.45


def test_schedule_persist_false_writes_nothing():
    _add_rule(enabled=1)
    with MortgageService() as s:
        out = s.schedule(1_000_000, 3.5, 360, None, False, start_month=12, start_day=1)
        assert out["run_id"] is None
        assert s.history() == []


# ---- 钉选 ----

def test_persisted_run_pins_rate_used():
    rid = _add_rule(enabled=1)
    with MortgageService() as s:
        out = s.schedule(1_000_000, 9.99, 360, None, True, start_month=12, start_day=1)
    # 事后改窗内利率
    conn = connect()
    repricing_rules.update(conn, rid, 11, 1, 2, 28, 1.01, 2.02, 1)
    rows = [dict(r) for r in conn.execute("SELECT * FROM calc_runs WHERE id=?", (out["run_id"],)).fetchall()]
    conn.close()
    payload = json.loads(rows[0]["input_json"])
    result = json.loads(rows[0]["result_json"])
    assert payload["annual_rate_used"] == 3.10
    assert result["annual_rate_used"] == 3.10
    assert result["monthly_payment"] == 4270.16
    assert payload["rule_id"] == rid and payload["window_hit"] is True
