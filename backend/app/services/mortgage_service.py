from app.db import connect
from app.engines.amortization import equal_payment_schedule
from app.engines.repricing import in_window
from app.repositories import loans, repricing_rules, runs, settings

class MortgageService:
    def __init__(self): self._c = connect()
    def close(self): self._c.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()
    def list_loans(self): return loans.list_all(self._c)
    def loan(self, lid): return loans.get(self._c, lid)
    def settings(self): return settings.get_map(self._c)
    def history(self, limit=50): return runs.list_recent(self._c, limit)
    def schedule(self, principal, annual_rate, months, loan_id, persist, preview_rows=12, start_month=None, start_day=None):
        # 提交了起息月日且存在启用规则时按重定价窗定价，否则退回请求体年利率
        rule = repricing_rules.get_enabled(self._c) if start_month is not None else None
        window_hit = None
        rule_id = None
        rate_used = annual_rate
        if rule:
            rule_id = rule["id"]
            window_hit = in_window(rule["start_month"], rule["start_day"], rule["end_month"], rule["end_day"], start_month, start_day)
            rate_used = rule["in_window_rate"] if window_hit else rule["out_window_rate"]
        full = equal_payment_schedule(principal, rate_used, months)
        out = {k: full[k] for k in ("monthly_payment", "total_interest", "total_payment")}
        out["preview"] = full["rows"][:preview_rows]
        out["row_count"] = len(full["rows"])
        out["window_hit"] = window_hit
        out["annual_rate_used"] = rate_used
        out["rule_id"] = rule_id
        rid = None
        if persist:
            # 钉选当时所用年利率与命中结果，事后改规则不回写该记录
            payload = {"principal": principal, "annual_rate": annual_rate, "months": months,
                       "start_month": start_month, "start_day": start_day,
                       "annual_rate_used": rate_used, "window_hit": window_hit, "rule_id": rule_id}
            rid = runs.insert(self._c, "schedule", payload, out, loan_id)
        return {"run_id": rid, **out}
    def dashboard(self):
        items = loans.list_all(self._c)
        return {"loan_count": len(items), "clean": len([x for x in items if "种子" not in x["name"]]), "dirty": len([x for x in items if "种子" in x["name"]])}
