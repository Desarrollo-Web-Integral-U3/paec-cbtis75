from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.core.rate_limit import limiter
from app.models.design_sprint import DesignSprintDay
from app.repositories.base_repository import BaseRepository
from app.schemas.design_sprint import (
    DesignSprintDayCreate,
    DesignSprintDayOut,
    DesignSprintDayFeedback,
)
from app.services.storage_service import get_storage_backend, validate_file

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
@limiter.limit("10/minute")
async def subir_evidencia(
    day_id: int,
    request: Request,
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Sube la evidencia del dia de Design Sprint a Cloudinary, guarda la URL
    publica y el public_id, y marca el dia como completado. Valida MIME y
    tamano antes de subir (OWASP: entrada no confiable + rubrica).
    """
    repo = BaseRepository(db, DesignSprintDay)
    day = repo.get_by_id(day_id)
    if not day:
        raise HTTPException(status_code=404, detail="Día de Design Sprint no encontrado.")

    contenido = await archivo.read()
    try:
        validate_file(
            filename=archivo.filename or "",
            content_type=archivo.content_type or "",
            size_bytes=len(contenido),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    backend = get_storage_backend()
    resultado = backend.upload(
        file_bytes=contenido,
        filename=archivo.filename or "archivo",
        folder=f"paec/evidencias/design-sprint/{day_id}",
    )

    day.evidencia_url = resultado.url
    day.evidencia_public_id = resultado.public_id
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
