from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.rate_limit import limiter
from app.middleware.audit_log import AuditLogMiddleware
from app.routers import (
    auth,
    teams,
    design_sprint,
    backlog,
    kanban,
    dailies,
    dashboard,
    uploads,
    cron,
)

settings = get_settings()

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

# --- Auditoria: registra metodo, ruta, user_id y timestamp por cada request ---
# GARANTIA: nunca lee el body ni registra contraseñas u otros datos sensibles.
app.add_middleware(AuditLogMiddleware)

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
app.include_router(uploads.router)
app.include_router(cron.router)


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "environment": settings.environment}
