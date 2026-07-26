from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.sprint import Sprint
from app.models.task import Task
from app.repositories.base_repository import BaseRepository
from app.repositories.task_repository import TaskRepository
from app.schemas.task import SprintCreate, SprintOut, TaskCreate, TaskOut, TaskUpdate

router = APIRouter(prefix="/api/v1", tags=["backlog"])


@router.post("/sprint", response_model=SprintOut, status_code=201)
def crear_sprint(
    payload: SprintCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("estudiante", "scrum_master")),
):
    repo = BaseRepository(db, Sprint)
    return repo.create(Sprint(**payload.model_dump()))


@router.post("/sprint/{sprint_id}/aprobar", response_model=SprintOut)
def aprobar_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("docente")),
):
    repo = BaseRepository(db, Sprint)
    sprint = repo.get_by_id(sprint_id)
    if not sprint:
        raise HTTPException(status_code=404, detail="Sprint no encontrado.")
    sprint.aprobado_por_docente = True
    return repo.update(sprint)


@router.post("/historia", response_model=TaskOut, status_code=201)
def crear_historia(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("estudiante", "scrum_master")),
):
    repo = BaseRepository(db, Task)
    return repo.create(Task(**payload.model_dump()))


@router.put("/historia/{historia_id}", response_model=TaskOut)
def actualizar_historia(
    historia_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("estudiante", "scrum_master")),
):
    repo = BaseRepository(db, Task)
    historia = repo.get_by_id(historia_id)
    if not historia:
        raise HTTPException(status_code=404, detail="Historia no encontrada.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(historia, field, value)

    return repo.update(historia)


@router.get("/sprint/{sprint_id}/historias", response_model=list[TaskOut])
def listar_historias_de_sprint(
    sprint_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return TaskRepository(db).list_by_sprint(sprint_id)


@router.get("/equipo/{team_id}/historias", response_model=list[TaskOut])
def listar_historias_por_equipo(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return TaskRepository(db).list_by_team(team_id)


@router.get("/equipo/{team_id}/sprints", response_model=list[SprintOut])
def listar_sprints_por_equipo(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = BaseRepository(db, Sprint)
    return db.query(Sprint).filter(Sprint.team_id == team_id).order_by(Sprint.numero_parcial.asc()).all()


@router.put("/historia/{historia_id}", response_model=TaskOut)
def actualizar_historia(
    historia_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("estudiante", "scrum_master")),
):
    """
    Actualiza solo los campos enviados en la petición (partial update).
    Los campos no incluidos en el body mantienen su valor actual en BD.
    Responde 404 si el id no existe.
    """
    repo = BaseRepository(db, Task)
    historia = repo.get_by_id(historia_id)
    if not historia:
        raise HTTPException(status_code=404, detail="Historia de usuario no encontrada.")

    # exclude_unset=True: solo itera los campos que el cliente envio explicitamente,
    # evitando sobrescribir con None campos que no venian en la peticion.
    cambios = payload.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(historia, campo, valor)

    return repo.update(historia)


@router.delete("/historia/{historia_id}", status_code=204)
def eliminar_historia(
    historia_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("estudiante", "scrum_master")),
):
    """
    Elimina la historia de usuario indicada.
    Responde 404 si el id no existe, 204 sin body si se eliminó correctamente.
    """
    repo = BaseRepository(db, Task)
    historia = repo.get_by_id(historia_id)
    if not historia:
        raise HTTPException(status_code=404, detail="Historia de usuario no encontrada.")

    repo.delete(historia)
