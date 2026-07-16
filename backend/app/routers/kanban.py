from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.task import Task, EstadoKanban
from app.repositories.base_repository import BaseRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import TaskMoveKanban, TaskApprove, TaskOut

router = APIRouter(prefix="/api/v1/historia", tags=["kanban"])


@router.get("/equipo/{team_id}/kanban", response_model=list[TaskOut])
def ver_tablero(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return TaskRepository(db).list_by_team(team_id)


@router.patch("/{task_id}/mover", response_model=TaskOut)
def mover_tarea(
    task_id: int,
    payload: TaskMoveKanban,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = BaseRepository(db, Task)
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    # REGLA DE NEGOCIO OBLIGATORIA: para mover a "terminado" es forzoso
    # traer evidencia o comentario. Se valida aquí, en el BackEnd, no solo
    # deshabilitando el botón en el FrontEnd.
    if payload.nuevo_estado == EstadoKanban.TERMINADO and not (
        payload.evidencia_url or payload.comentario
    ):
        raise HTTPException(
            status_code=400,
            detail="Para marcar como Terminado debes adjuntar evidencia o comentario.",
        )

    task.estado_kanban = payload.nuevo_estado
    if payload.evidencia_url:
        task.evidencia_url = payload.evidencia_url
    if payload.comentario:
        task.comentario = payload.comentario

    return repo.update(task)


@router.patch("/{task_id}/aprobar", response_model=TaskOut)
def aprobar_evidencia(
    task_id: int,
    payload: TaskApprove,
    db: Session = Depends(get_db),
    # Solo el Scrum Master (o el docente) puede aprobar evidencia
    current_user=Depends(require_role("scrum_master", "docente")),
):
    repo = BaseRepository(db, Task)
    task = repo.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Tarea no encontrada.")

    task.aprobado_por_scrum_master = payload.aprobado_por_scrum_master
    return repo.update(task)
