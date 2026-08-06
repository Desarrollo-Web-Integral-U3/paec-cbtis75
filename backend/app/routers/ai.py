"""
Endpoints de IA. Actualmente:

- POST /api/v1/ai/resumen-semanal/{team_id} → resumen de dailies con Groq.

Consume el servicio de terceros Groq (LLM compatible con OpenAI) — cuenta
como segundo web service externo del proyecto (el primero es SMTP para
notificaciones). Ver `app/services/ai_summary_service.py`.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.team import Team, TeamMember
from app.services.ai_summary_service import generar_resumen_semanal

router = APIRouter(prefix="/api/v1/ai", tags=["ai"])


@router.post("/resumen-semanal/{team_id}")
def resumen_semanal_dailies(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Genera un resumen ejecutivo (Markdown) de los dailies del equipo en
    los últimos 7 días, usando el LLM Groq.

    Autorización: el usuario debe ser miembro del equipo, o tener rol
    `docente`. Cualquier otro caso devuelve 403.
    """
    team = db.query(Team).filter(Team.id == team_id).first()
    if team is None:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    es_miembro = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
        )
        .first()
        is not None
    )
    if not es_miembro and current_user.rol.value != "docente":
        raise HTTPException(
            status_code=403,
            detail="Solo miembros del equipo o docentes pueden generar el resumen.",
        )

    return generar_resumen_semanal(db, team_id)
