"""
Schemas Pydantic para el modulo de equipos.

Reglas de negocio (issue #12):
- Un equipo tiene entre 2 y 4 integrantes.
- Cada integrante tiene un rol_scrum valido.
- Debe haber exactamente 1 Scrum Master.
- Puede haber 0 o 1 Product Owner (opcional).
- El resto son Developers.
- No se puede repetir el mismo email en el mismo equipo.
- Los integrantes se referencian por email (el backend resuelve email -> user_id).
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.design_sprint import DesignSprintDayOut


class RolScrum(str, Enum):
    """
    Roles Scrum validos dentro de un equipo.
    NO confundir con el rol de usuario a nivel de aplicacion (estudiante,
    scrum_master, docente), que vive en app/models/user.py::RolUsuario.
    Este enum aplica solo a la posicion dentro de un equipo especifico.

    Se aceptan variantes de Developer con especialidad (Dev FrontEnd,
    Dev BackEnd) porque el frontend permite capturarlas al crear el equipo
    y el modelo Team las guarda tal cual en la columna `rol_scrum`.
    """
    SCRUM_MASTER = "Scrum Master"
    PRODUCT_OWNER = "Product Owner"
    DEVELOPER = "Developer"
    DEV_FRONTEND = "Dev FrontEnd"
    DEV_BACKEND = "Dev BackEnd"


class TeamMemberInput(BaseModel):
    """Datos que envia el frontend por cada integrante al crear el equipo."""
    email: EmailStr
    rol_scrum: RolScrum

    model_config = ConfigDict(extra="forbid")


class TeamCreate(BaseModel):
    """Payload de creacion de equipo."""
    nombre_proyecto: str = Field(min_length=3, max_length=150)
    descripcion_proyecto: str | None = Field(default=None, max_length=500)
    grupo: str | None = Field(default=None, max_length=30)
    # Capacidad total del equipo en horas para el sprint.
    # Se puede declarar al crear el equipo o actualizar despues.
    horas_disponibles: int = Field(default=0, ge=0)
    members: list[TeamMemberInput] = Field(min_length=2, max_length=4)

    model_config = ConfigDict(extra="forbid")

    @field_validator("nombre_proyecto")
    @classmethod
    def _nombre_no_vacio(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("El nombre del proyecto no puede estar vacio.")
        return v

    @model_validator(mode="after")
    def _validar_reglas_scrum(self) -> "TeamCreate":
        """Aplica las reglas de negocio Scrum: 1 SM, 0-1 PO, sin emails repetidos."""
        emails = [m.email.lower() for m in self.members]
        if len(emails) != len(set(emails)):
            raise ValueError("No se puede repetir el mismo email en el equipo.")

        roles = [m.rol_scrum for m in self.members]
        n_sm = roles.count(RolScrum.SCRUM_MASTER)
        n_po = roles.count(RolScrum.PRODUCT_OWNER)

        if n_sm != 1:
            raise ValueError(
                "El equipo debe tener exactamente un Scrum Master."
            )
        if n_po > 1:
            raise ValueError(
                "El equipo no puede tener mas de un Product Owner."
            )
        return self


class TeamMemberOut(BaseModel):
    """Representacion de un integrante dentro del response de un equipo."""
    user_id: int
    email: EmailStr
    nombre_completo: str
    rol_scrum: RolScrum

    model_config = ConfigDict(from_attributes=True)


class TeamOut(BaseModel):
    """Response completo de un equipo (incluye integrantes con su rol Scrum)."""
    id: int
    nombre_proyecto: str
    descripcion_proyecto: str | None
    grupo: str | None
    horas_disponibles: int
    members: list[TeamMemberOut]
    # Issue #8: los 5 dias del Design Sprint se incluyen en la respuesta
    # para que el frontend no necesite una segunda llamada al crear el equipo.
    design_sprint_days: list[DesignSprintDayOut] = []

    model_config = ConfigDict(from_attributes=True)


class CapacidadOut(BaseModel):
    """
    Response del endpoint GET /equipo/{id}/capacidad.
    Permite al frontend comparar la carga ya asignada contra la
    capacidad total del equipo (base para las vistas del dashboard).
    """
    team_id: int
    horas_disponibles: int
    horas_asignadas: int   # suma de tiempo_estimado_horas de todas las tareas
    horas_restantes: int   # horas_disponibles - horas_asignadas (negativo = sobrecarga)

    model_config = ConfigDict(from_attributes=True)


class ResumenEquipoOut(BaseModel):
    """
    Resumen de avance de un equipo para el dashboard general del docente.
    Incluye story points planeados vs. completados para que el docente
    pueda comparar el progreso de todos los equipos del curso en una vista.
    """
    team_id: int
    nombre_proyecto: str
    grupo: str | None
    total_tareas: int
    story_points_planeados: int
    story_points_completados: int
    # Porcentaje de avance: 0-100. Se calcula en el servicio para evitar
    # division por cero en el frontend cuando planeados == 0.
    porcentaje_avance: float

    model_config = ConfigDict(from_attributes=True)
