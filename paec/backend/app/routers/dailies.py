from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.daily import Daily
from app.repositories.base_repository import BaseRepository
from app.schemas.daily import DailyCreate, DailyOut

router = APIRouter(prefix="/api/v1/daily", tags=["dailies"])


@router.post("/", response_model=DailyOut, status_code=201)
def registrar_daily(
    payload: DailyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    repo = BaseRepository(db, Daily)
    daily = Daily(user_id=current_user.id, **payload.model_dump())
    return repo.create(daily)


@router.get("/equipo/{team_id}", response_model=list[DailyOut])
def listar_dailies_equipo(
    team_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Daily).filter(Daily.team_id == team_id).order_by(Daily.fecha.desc()).all()
