from pydantic import BaseModel, ConfigDict


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

    model_config = ConfigDict(from_attributes=True)
