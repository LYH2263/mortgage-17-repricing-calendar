import json
import pytest
from pydantic import ValidationError

from app import db, seed
from app.errors import ConflictError
from app.modules.rate_float import in_window, resolve_rate, valid_month_day
from app.schemas.schedule import ScheduleRequest
from app.services.mortgage_service import MortgageService


# ---------- 纯逻辑 ----------

@pytest.mark.parametrize("m,d,ok", [
    (1, 1, True), (12, 31, True), (2, 29, True), (2, 30, False),
    (0, 1, False), (13, 1, False), (4, 31, False), (6, 30, True),
])
def test_valid_month_day(m, d, ok):
    assert valid_month_day(m, d) is ok


def test_in_window_normal():
    # 03-01 ~ 05-31 不跨年
    assert in_window(3, 1, 3, 1, 5, 31)       # 起点含
    assert in_window(5, 31, 3, 1, 5, 31)      # 终点含
    assert in_window(4, 15, 3, 1, 5, 31)
    assert not in_window(2, 28, 3, 1, 5, 31)
    assert not in_window(6, 1, 3, 1, 5, 31)


def test_in_window_cross_year():
    # 12-01 ~ 02-28 跨年
    assert in_window(12, 1, 12, 1, 2, 28)     # 起点含
    assert in_window(2, 28, 12, 1, 2, 28)     # 终点含
    assert in_window(1, 15, 12, 1, 2, 28)
    assert not in_window(6, 15, 12, 1, 2, 28)
    assert not in_window(11, 30, 12, 1, 2, 28)
    assert not in_window(3, 1, 12, 1, 2, 28)


def test_in_window_single_day():
    assert in_window(7, 7, 7, 7, 7, 7)
    assert not in_window(7, 8, 7, 7, 7, 7)


def test_in_window_leap_boundary():
    assert in_window(2, 29, 2, 29, 3, 1)
    assert not in_window(2, 28, 2, 29, 3, 1)


def test_resolve_rate():
    rule = {"start_month": 12, "start_day": 1, "end_month": 2, "end_day": 28,
            "in_rate": 3.6, "out_rate": 4.2}
    assert resolve_rate(rule, 1, 10) == (True, 3.6)
    assert resolve_rate(rule, 6, 10) == (False, 4.2)


# ---------- DB / 服务层 ----------

@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MortgageService() as s:
        yield s


def _rule(enabled=True, start=(12, 1), end=(2, 28), rin=3.6, rout=4.2):
    return {"start_month": start[0], "start_day": start[1],
            "end_month": end[0], "end_day": end[1],
            "in_rate": rin, "out_rate": rout, "enabled": enabled}


def test_seed_has_one_enabled_rule(svc):
    rules = svc.list_rate_window_rules()
    assert len(rules) == 1
    assert rules[0]["enabled"] is True
    assert rules[0]["id"] == 1


def test_create_enabled_conflict_names_both_ids(svc):
    with pytest.raises(ConflictError) as ei:
        svc.create_rate_window_rule(_rule(enabled=True))
    msg = str(ei.value)
    assert "#1" in msg and "#2" in msg
    # 冲突后不留残行
    assert len(svc.list_rate_window_rules()) == 1


def test_create_disabled_ok(svc):
    row = svc.create_rate_window_rule(_rule(enabled=False, start=(3, 1), end=(5, 31)))
    assert row["enabled"] is False
    assert len(svc.list_rate_window_rules()) == 2


def test_update_self_enabled_ok(svc):
    row = svc.update_rate_window_rule(1, _rule(enabled=True, rin=3.1))
    assert row["in_rate"] == 3.1 and row["enabled"] is True


def test_enable_other_conflicts(svc):
    svc.create_rate_window_rule(_rule(enabled=False, start=(3, 1), end=(5, 31)))
    with pytest.raises(ConflictError) as ei:
        svc.update_rate_window_rule(2, _rule(enabled=True, start=(3, 1), end=(5, 31)))
    msg = str(ei.value)
    assert "#1" in msg and "#2" in msg


def test_disable_then_enable_other(svc):
    svc.create_rate_window_rule(_rule(enabled=False, start=(3, 1), end=(5, 31)))
    assert svc.disable_rate_window_rule(1)["enabled"] is False
    assert svc.update_rate_window_rule(2, _rule(enabled=True, start=(3, 1), end=(5, 31)))["enabled"] is True
    assert svc.get_rate_window_rule(1)["enabled"] is False


def test_missing_rule_returns_none(svc):
    assert svc.update_rate_window_rule(99, _rule()) is None
    assert svc.disable_rate_window_rule(99) is None


# ---------- 测算利率解析 ----------

def test_schedule_hit_in_window(svc):
    out = svc.schedule(800000, 4.9, 360, None, False, value_month=1, value_day=15)
    assert out["rate_window_hit"] is True
    assert out["applied_annual_rate"] == 3.6
    assert out["rate_rule_id"] == 1


def test_schedule_miss_out_window(svc):
    out = svc.schedule(800000, 4.9, 360, None, False, value_month=6, value_day=15)
    assert out["rate_window_hit"] is False
    assert out["applied_annual_rate"] == 4.2


def test_schedule_boundaries(svc):
    assert svc.schedule(800000, 4.9, 12, None, False, value_month=12, value_day=1)["rate_window_hit"] is True
    assert svc.schedule(800000, 4.9, 12, None, False, value_month=2, value_day=28)["rate_window_hit"] is True
    assert svc.schedule(800000, 4.9, 12, None, False, value_month=3, value_day=1)["rate_window_hit"] is False


def test_schedule_without_value_date_falls_back(svc):
    out = svc.schedule(800000, 4.9, 360, None, False)
    assert out["rate_window_hit"] is None
    assert out["applied_annual_rate"] == 4.9
    assert out["rate_rule_id"] is None


def test_schedule_disabled_rule_falls_back(svc):
    svc.disable_rate_window_rule(1)
    out = svc.schedule(800000, 4.9, 360, None, False, value_month=1, value_day=15)
    assert out["rate_window_hit"] is None
    assert out["applied_annual_rate"] == 4.9


def test_schedule_half_pair_rejected():
    with pytest.raises(ValidationError):
        ScheduleRequest(principal=1, annual_rate=3, months=12, value_month=1)


# ---------- persist 与钉选 ----------

def test_persist_false_writes_nothing(svc):
    before = len(svc.history(100))
    out = svc.schedule(800000, 4.9, 360, None, False, value_month=1, value_day=15)
    after = len(svc.history(100))
    assert out["run_id"] is None
    assert before == after == 1  # 仅种子记录


def test_persist_pins_rate_and_survives_rule_edit(svc):
    out = svc.schedule(800000, 4.9, 360, None, True, value_month=1, value_day=15)
    rid = out["run_id"]
    assert rid is not None
    rows = {h["id"]: h for h in svc.history(100)}
    payload = json.loads(rows[rid]["input_json"])
    assert payload["annual_rate"] == 3.6              # 钉选窗内利率
    assert payload["requested_annual_rate"] == 4.9
    assert payload["rate_window_hit"] is True

    # 事后修改窗内利率，历史记录不变
    svc.update_rate_window_rule(1, _rule(enabled=True, rin=3.1))
    rows2 = {h["id"]: h for h in svc.history(100)}
    payload2 = json.loads(rows2[rid]["input_json"])
    result2 = json.loads(rows2[rid]["result_json"])
    assert payload2["annual_rate"] == 3.6
    assert result2["applied_annual_rate"] == 3.6


# ---------- HTTP 级 ----------

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "http.db")
    seed.init_db()
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


def test_http_conflict_names_both_ids(client):
    body = _rule(enabled=True)
    r = client.post("/api/rate-window-rules", json=body)
    assert r.status_code == 409
    detail = r.json()["detail"]
    assert "#1" in detail and "#2" in detail


def test_http_update_missing_404(client):
    r = client.post("/api/rate-window-rules/99", json=_rule())
    assert r.status_code == 404


def test_http_disable_missing_404(client):
    r = client.post("/api/rate-window-rules/99/disable")
    assert r.status_code == 404


def test_http_schedule_half_pair_422(client):
    r = client.post("/api/schedule", json={"principal": 800000, "annual_rate": 4.9,
                                           "months": 360, "value_month": 1})
    assert r.status_code == 422


def test_http_schedule_hit(client):
    r = client.post("/api/schedule", json={"principal": 800000, "annual_rate": 4.9,
                                           "months": 360, "persist": False,
                                           "value_month": 1, "value_day": 15})
    assert r.status_code == 200
    body = r.json()
    assert body["rate_window_hit"] is True
    assert body["applied_annual_rate"] == 3.6
    assert "monthly_payment" in body and "total_interest" in body
