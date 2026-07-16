from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.alert import TipoAlerta


class AlertOut(BaseModel):
    id: int
    team_id: int
    tipo: TipoAlerta
    mensaje: str
    fecha: datetime
    atendida: bool

    model_config = ConfigDict(from_attributes=True)
