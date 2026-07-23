from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.design_sprint import DiaDesignSprint


class DesignSprintDayCreate(BaseModel):
    team_id: int
    dia: DiaDesignSprint
    fecha_planeada: datetime
    plan_descripcion: str


class DesignSprintDayFeedback(BaseModel):
    comentario_docente: str


class DesignSprintDayOut(BaseModel):
    id: int
    team_id: int
    dia: DiaDesignSprint
    fecha_planeada: datetime | None
    plan_descripcion: str | None
    evidencia_url: str | None
    evidencia_public_id: str | None
    comentario_docente: str | None
    completado: int

    model_config = ConfigDict(from_attributes=True)