from app.db import connect
from app.engines.amortization import equal_payment_schedule
from app.errors import ConflictError
from app.modules.rate_float import resolve_rate
from app.repositories import loans, runs, settings, rate_window_rules

class MortgageService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_loans(self): return loans.list_all(self._c)
    def loan(self, lid): return loans.get(self._c, lid)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)

    # ---- 起息日重定价窗规则 ----
    def list_rate_window_rules(self): return rate_window_rules.list_all(self._c)
    def get_rate_window_rule(self, rid): return rate_window_rules.get(self._c, rid)

    def create_rate_window_rule(self, data):
        new_id = rate_window_rules.insert(self._c, data, commit=False)
        if data["enabled"]:
            existing = rate_window_rules.active(self._c)
            if existing and existing["id"] != new_id:
                self._c.rollback()
                raise ConflictError(
                    f"仅允许一条启用规则：现有启用规则 #{existing['id']} 与本次规则 #{new_id} 冲突")
        self._c.commit()
        return rate_window_rules.get(self._c, new_id)

    def update_rate_window_rule(self, rid, data):
        if not rate_window_rules.get(self._c, rid):
            return None
        if data["enabled"]:
            existing = rate_window_rules.active(self._c)
            if existing and existing["id"] != rid:
                raise ConflictError(
                    f"仅允许一条启用规则：现有启用规则 #{existing['id']} 与本次规则 #{rid} 冲突")
        rate_window_rules.update(self._c, rid, data)
        return rate_window_rules.get(self._c, rid)

    def disable_rate_window_rule(self, rid):
        if not rate_window_rules.get(self._c, rid):
            return None
        rate_window_rules.disable(self._c, rid)
        return rate_window_rules.get(self._c, rid)

    def schedule(self, principal, annual_rate, months, loan_id, persist,
                 preview_rows=12, value_month=None, value_day=None):
        # 起息月日 + 启用规则同时具备才参与定价；否则回退请求体年利率
        hit, rule_id = None, None
        if value_month is not None and value_day is not None:
            rule = rate_window_rules.active(self._c)
            if rule:
                hit, applied = resolve_rate(rule, value_month, value_day)
                rule_id = rule["id"]
            else:
                applied = annual_rate
        else:
            applied = annual_rate
        full = equal_payment_schedule(principal, applied, months)
        out = {k: full[k] for k in ("monthly_payment", "total_interest", "total_payment")}
        out["preview"] = full["rows"][:preview_rows]
        out["row_count"] = len(full["rows"])
        out["applied_annual_rate"] = applied
        out["rate_window_hit"] = hit
        out["rate_rule_id"] = rule_id
        rid = None
        if persist:
            payload = {
                "principal": principal,
                "annual_rate": applied,            # 钉选当时实际所用年利率
                "requested_annual_rate": annual_rate,
                "months": months,
                "value_month": value_month,
                "value_day": value_day,
                "rate_window_hit": hit,
                "rate_rule_id": rule_id,
            }
            rid = runs.insert(self._c, "schedule", payload, out, loan_id)
        return {"run_id": rid, **out}

    def dashboard(self):
        items = loans.list_all(self._c)
        return {"loan_count": len(items), "clean": len([x for x in items if "种子" not in x["name"]]), "dirty": len([x for x in items if "种子" in x["name"]])}
