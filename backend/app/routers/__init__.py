from fastapi import APIRouter
from app.routers import dashboard, history, loans, rate_window, schedule, settings
api = APIRouter(prefix="/api")
for r in (dashboard, loans, schedule, history, settings, rate_window): api.include_router(r.router)
