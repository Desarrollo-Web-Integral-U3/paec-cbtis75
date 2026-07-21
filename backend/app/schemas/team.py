from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.schemas.design_sprint import DesignSprintDayOut


class TeamMemberCreate(BaseModel):
    user_id: int
    rol_scrum: str


class TeamCreate(BaseModel):
    nombre_proyecto: str
    descripcion_proyecto: str | None = None
    grupo: str | None = None
    members: list[TeamMemberCreate]


class TeamOut(BaseModel):
    id: int
    nombre_proyecto: str
    descripcion_proyecto: str | None
    grupo: str | None
    # Issue #8: los 5 días del Design Sprint se incluyen en la respuesta
    # para que el frontend no necesite una segunda llamada al crear el equipo.
    design_sprint_days: list[DesignSprintDayOut] = []

    model_config = ConfigDict(from_attributes=True)
