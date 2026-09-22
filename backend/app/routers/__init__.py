from fastapi import APIRouter
from app.routers import dashboard, history, loans, repricing, schedule, settings
api = APIRouter(prefix="/api")
for r in (dashboard, loans, schedule, history, settings, repricing): api.include_router(r.router)
