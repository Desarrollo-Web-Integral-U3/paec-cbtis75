from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.database import Base, engine
from app.routers import auth, teams, design_sprint, backlog, kanban, dailies, dashboard

settings = get_settings()

# --- Rate limiting global (cubre "Falta de Rate Limiting" del OWASP Top 10) ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title=settings.app_name)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS: solo orígenes explícitamente permitidos, nunca "*" en producción ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)

# En desarrollo: crea las tablas automáticamente.
# En producción: usar Alembic (alembic upgrade head) y NO Base.metadata.create_all.
if settings.environment == "development":
    Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(design_sprint.router)
app.include_router(backlog.router)
app.include_router(kanban.router)
app.include_router(dailies.router)
app.include_router(dashboard.router)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}
