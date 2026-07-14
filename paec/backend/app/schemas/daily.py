from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DailyCreate(BaseModel):
    team_id: int
    que_hice_ayer: str
    que_hare_hoy: str
    impedimentos: str | None = None
    acuerdos: str | None = None


class DailyOut(BaseModel):
    id: int
    team_id: int
    user_id: int
    fecha: datetime
    que_hice_ayer: str
    que_hare_hoy: str
    impedimentos: str | None
    acuerdos: str | None

    model_config = ConfigDict(from_attributes=True)
