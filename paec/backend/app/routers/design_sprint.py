from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.design_sprint import DesignSprintDay
from app.repositories.base_repository import BaseRepository
from app.schemas.design_sprint import (
    DesignSprintDayCreate,
    DesignSprintDayOut,
    DesignSprintDayFeedback,
)

router = APIRouter(prefix="/api/v1/design-sprint", tags=["design-sprint"])


@router.post("/", response_model=DesignSprintDayOut, status_code=201)
def planear_dia(
    payload: DesignSprintDayCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = BaseRepository(db, DesignSprintDay)
    day = DesignSprintDay(**payload.model_dump())
    return repo.create(day)


@router.post("/{day_id}/evidencia", response_model=DesignSprintDayOut)
def subir_evidencia(
    day_id: int,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    NOTA DE IMPLEMENTACIÓN: aquí solo se guarda la referencia (nombre/ruta).
    En producción, subir 'archivo' a un almacenamiento de objetos (S3,
    Supabase Storage, Cloudinary, etc.) y guardar la URL resultante —
    nunca servir archivos subidos directamente desde el mismo dominio de
    la API sin validar tipo/tamaño (riesgo de XSS almacenado / malware).
    """
    repo = BaseRepository(db, DesignSprintDay)
    day = repo.get_by_id(day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Día de Design Sprint no encontrado.")

    day.evidencia_url = f"/uploads/design-sprint/{day_id}/{archivo.filename}"
    day.completado = 1
    return repo.update(day)


@router.post("/{day_id}/feedback", response_model=DesignSprintDayOut)
def dejar_feedback(
    day_id: int,
    payload: DesignSprintDayFeedback,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("docente")),
):
    repo = BaseRepository(db, DesignSprintDay)
    day = repo.get_by_id(day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Día de Design Sprint no encontrado.")

    day.comentario_docente = payload.comentario_docente
    return repo.update(day)


@router.get("/equipo/{team_id}", response_model=list[DesignSprintDayOut])
def listar_por_equipo(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(DesignSprintDay).filter(DesignSprintDay.team_id == team_id).all()
