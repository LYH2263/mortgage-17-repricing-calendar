from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app import seed
from app.errors import ConflictError
from app.routers import api
app = FastAPI(title="Mortgage", version="0.2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.exception_handler(ConflictError)
def _conflict_handler(_: Request, exc: ConflictError):
    return JSONResponse(status_code=409, content={"detail": str(exc)})

@app.on_event("startup")
def _startup(): seed.init_db()
app.include_router(api)
@app.get("/api/health")
def health(): return {"ok": True, "project": "mortgage"}
