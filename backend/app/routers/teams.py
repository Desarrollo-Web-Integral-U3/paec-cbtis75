"""
Router de equipos.

Endpoints:
- POST /api/v1/equipo/          Crea un equipo con 2-4 integrantes.
- GET  /api/v1/equipo/{team_id} Consulta el equipo y sus integrantes.

Notas de diseno (issue #12):
- El payload de creacion usa emails, no user_ids: el frontend no tiene
  por que conocer los ids internos. Aca se resuelven a user_id via
  UserRepository. Si algun email no existe, se responde 422 listando
  los correos faltantes.
- La respuesta expande cada integrante con {user_id, email,
  nombre_completo, rol_scrum} para que el frontend confirme visualmente
  que el equipo quedo bien registrado (criterio de aceptacion del issue).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.design_sprint import DesignSprintDay, DiaDesignSprint
from app.models.team import Team, TeamMember
from app.repositories.base_repository import BaseRepository
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.team import TeamCreate, TeamMemberOut, TeamOut, CapacidadOut

router = APIRouter(prefix="/api/v1/equipo", tags=["equipos"])


def _serialize_team(team: Team) -> TeamOut:
    """
    Convierte una entidad Team (con sus relaciones cargadas) al schema TeamOut.
    Aplana user.email y user.nombre_completo desde el TeamMember para el response.
    """
    miembros = [
        TeamMemberOut(
            user_id=m.user_id,
            email=m.user.email,
            nombre_completo=m.user.nombre_completo,
            rol_scrum=m.rol_scrum,
        )
        for m in team.members
    ]
    return TeamOut(
        id=team.id,
        nombre_proyecto=team.nombre_proyecto,
        descripcion_proyecto=team.descripcion_proyecto,
        grupo=team.grupo,
        horas_disponibles=team.horas_disponibles,
        members=miembros,
        design_sprint_days=team.design_sprint_days,
    )


@router.post("/", response_model=TeamOut, status_code=status.HTTP_201_CREATED)
def crear_equipo(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crea un equipo con 2-4 integrantes y su rol Scrum.

    Reglas validadas en el schema (TeamCreate):
    - min 2 y max 4 integrantes.
    - Exactamente 1 Scrum Master.
    - Maximo 1 Product Owner.
    - Emails unicos dentro del equipo.

    Reglas validadas aca:
    - Todos los emails deben existir en la tabla users. Si falta alguno se
      responde 422 con detail={"mensaje": "...", "emails_no_encontrados": [...]}.
    """
    user_repo = UserRepository(db)

    # Resolver emails -> usuarios. Se hace UNA consulta por email; la tabla
    # tiene indice unique en email, asi que el costo es O(k) con k = # miembros.
    usuarios_por_email: dict[str, object] = {}
    emails_faltantes: list[str] = []
    for m in payload.members:
        usuario = user_repo.get_by_email(m.email)
        if usuario is None:
            emails_faltantes.append(m.email)
        else:
            usuarios_por_email[m.email] = usuario

    if emails_faltantes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "mensaje": "Hay correos que no corresponden a usuarios registrados.",
                "emails_no_encontrados": emails_faltantes,
            },
        )

    team = Team(
        nombre_proyecto=payload.nombre_proyecto,
        descripcion_proyecto=payload.descripcion_proyecto,
        grupo=payload.grupo,
    )
    db.add(team)
    db.flush()  # obtiene team.id sin cerrar la transaccion

    for m in payload.members:
        usuario = usuarios_por_email[m.email]
        db.add(
            TeamMember(
                team_id=team.id,
                user_id=usuario.id,
                rol_scrum=m.rol_scrum.value,
            )
        )

    # Issue #8: auto-crear los 5 dias del Design Sprint en la misma transaccion.
    # Si el commit falla, los dias tambien se revierten (atomicidad).
    for dia in DiaDesignSprint:
        db.add(DesignSprintDay(team_id=team.id, dia=dia))

    db.commit()
    db.refresh(team)
    return _serialize_team(team)


@router.get("/{team_id}", response_model=TeamOut)
def obtener_equipo(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Regresa el equipo con sus integrantes (user_id, email, nombre, rol_scrum)
    y los dias del Design Sprint. Solo miembros del equipo o docente pueden
    consultarlo (control de BOLA - OWASP).
    """
    repo = BaseRepository(db, Team)
    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    es_miembro = any(m.user_id == current_user.id for m in team.members)
    if not es_miembro and current_user.rol.value != "docente":
        raise HTTPException(status_code=403, detail="No autorizado para ver este equipo.")

    return _serialize_team(team)


@router.get("/{team_id}/capacidad", response_model=CapacidadOut)
def obtener_capacidad(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Devuelve la capacidad del equipo vs el esfuerzo ya asignado.
    - horas_disponibles: las que el equipo declaro al crear/actualizar el equipo.
    - horas_asignadas:   suma de tiempo_estimado_horas de TODAS sus tareas.
    - horas_restantes:   diferencia (negativa = sobrecarga).
    Base para las vistas de capacidad del dashboard.
    """
    repo = BaseRepository(db, Team)
    team = repo.get_by_id(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Equipo no encontrado.")

    horas_asignadas = TaskRepository(db).sum_horas_estimadas(team_id)

    return CapacidadOut(
        team_id=team_id,
        horas_disponibles=team.horas_disponibles,
        horas_asignadas=horas_asignadas,
        horas_restantes=team.horas_disponibles - horas_asignadas,
    )
