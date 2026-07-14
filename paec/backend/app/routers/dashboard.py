from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.services.alert_service import AlertService
from app.services.dashboard_service import DashboardService
from app.schemas.alert import AlertOut

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get("/equipo/{team_id}/dashboard")
def dashboard_equipo(
    team_id: int,
    db: Session = Depends(get_db),
    # Solo docente y Scrum Master ven el panel de avance
    current_user=Depends(require_role("docente", "scrum_master")),
):
    return DashboardService(db).resumen_equipo(team_id)


@router.post("/equipo/{team_id}/evaluar-alertas", response_model=list[AlertOut])
def evaluar_alertas(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("docente", "scrum_master")),
):
    """
    Dispara la evaluación de alertas (Strategy) para un equipo. En
    producción esto normalmente lo llama un cron/GitHub Action/Celery
    beat una vez al día, no el usuario manualmente.
    """
    return AlertService(db).evaluar_equipo(team_id)
