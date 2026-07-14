from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.team import Team, TeamMember
from app.repositories.base_repository import BaseRepository
from app.schemas.team import TeamCreate, TeamOut

router = APIRouter(prefix="/api/v1/equipo", tags=["equipos"])


@router.post("/", response_model=TeamOut, status_code=201)
def crear_equipo(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = BaseRepository(db, Team)
    team = Team(
        nombre_proyecto=payload.nombre_proyecto,
        descripcion_proyecto=payload.descripcion_proyecto,
        grupo=payload.grupo,
    )
    db.add(team)
    db.flush()  # obtiene team.id sin cerrar la transacción

    for m in payload.members:
        db.add(TeamMember(team_id=team.id, user_id=m.user_id, rol_scrum=m.rol_scrum))

    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}", response_model=TeamOut)
def obtener_equipo(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # PRUEBA DE BOLA (Actividad 2): este endpoint NO filtra por "mis equipos",
    # así que en producción se debe verificar que current_user pertenece al
    # team_id solicitado (o es docente) antes de regresar el resultado.
    repo = BaseRepository(db, Team)
    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    es_miembro = any(m.user_id == current_user.id for m in team.members)
    if not es_miembro and current_user.rol != "docente":
        raise HTTPException(status_code=403, detail="No autorizado para ver este equipo.")

    return team
