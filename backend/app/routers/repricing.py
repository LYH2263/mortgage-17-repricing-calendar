from fastapi import APIRouter, HTTPException
from app.db import connect
from app.repositories import repricing_rules
from app.schemas.repricing import RepricingRuleIn

router = APIRouter()


def _window_label(rule):
    return f"{rule['start_month']:02d}-{rule['start_day']:02d}~{rule['end_month']:02d}-{rule['end_day']:02d}"


def _check_enabled_conflict(conn, enabled, self_id=None, incoming_label=""):
    """同一时刻只允许一条启用规则；冲突时 409 并点名两条标识。"""
    if not enabled:
        return
    other = repricing_rules.get_enabled(conn)
    if other and other["id"] != self_id:
        who = f"规则#{self_id}" if self_id is not None else f"新规则({incoming_label})"
        raise HTTPException(
            409,
            f"启用冲突：{who} 与已启用的规则#{other['id']}（窗 {_window_label(other)}）不能同时启用，"
            "同一时刻只允许一条启用规则",
        )


@router.get("/repricing/rules")
def list_rules():
    conn = connect()
    try:
        return {"items": repricing_rules.list_all(conn)}
    finally:
        conn.close()


@router.post("/repricing/rules", status_code=201)
def create_rule(body: RepricingRuleIn):
    conn = connect()
    try:
        label = f"{body.start_month:02d}-{body.start_day:02d}~{body.end_month:02d}-{body.end_day:02d}"
        _check_enabled_conflict(conn, body.enabled, incoming_label=label)
        rid = repricing_rules.insert(
            conn, body.start_month, body.start_day, body.end_month, body.end_day,
            body.in_window_rate, body.out_window_rate, body.enabled)
        return repricing_rules.get(conn, rid)
    finally:
        conn.close()


@router.put("/repricing/rules/{rule_id}")
def update_rule(rule_id: int, body: RepricingRuleIn):
    conn = connect()
    try:
        if not repricing_rules.get(conn, rule_id):
            raise HTTPException(404, f"规则#{rule_id} 不存在")
        _check_enabled_conflict(conn, body.enabled, self_id=rule_id)
        repricing_rules.update(
            conn, rule_id, body.start_month, body.start_day, body.end_month, body.end_day,
            body.in_window_rate, body.out_window_rate, body.enabled)
        return repricing_rules.get(conn, rule_id)
    finally:
        conn.close()


@router.post("/repricing/rules/{rule_id}/disable")
def disable_rule(rule_id: int):
    conn = connect()
    try:
        if not repricing_rules.get(conn, rule_id):
            raise HTTPException(404, f"规则#{rule_id} 不存在")
        repricing_rules.set_enabled(conn, rule_id, False)
        return repricing_rules.get(conn, rule_id)
    finally:
        conn.close()
