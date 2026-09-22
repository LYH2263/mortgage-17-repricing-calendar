from fastapi import APIRouter, HTTPException
from app.schemas.rate_window import RateWindowRuleBody
from app.services.mortgage_service import MortgageService

router = APIRouter()


def _data(body: RateWindowRuleBody) -> dict:
    return body.model_dump()


@router.get("/rate-window-rules")
def list_rules():
    with MortgageService() as s:
        return {"items": s.list_rate_window_rules()}


@router.post("/rate-window-rules", status_code=201)
def create_rule(body: RateWindowRuleBody):
    with MortgageService() as s:
        return s.create_rate_window_rule(_data(body))


@router.post("/rate-window-rules/{rid}")
def update_rule(rid: int, body: RateWindowRuleBody):
    with MortgageService() as s:
        row = s.update_rate_window_rule(rid, _data(body))
        if not row:
            raise HTTPException(404)
        return row


@router.post("/rate-window-rules/{rid}/disable")
def disable_rule(rid: int):
    with MortgageService() as s:
        row = s.disable_rate_window_rule(rid)
        if not row:
            raise HTTPException(404)
        return row
