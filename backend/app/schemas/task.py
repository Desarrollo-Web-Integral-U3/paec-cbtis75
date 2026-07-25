from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.task import EstadoKanban, Prioridad


class SprintCreate(BaseModel):
    team_id: int
    numero_parcial: int
    fecha_inicio: datetime
    fecha_fin: datetime


class SprintOut(BaseModel):
    id: int
    team_id: int
    numero_parcial: int
    fecha_inicio: datetime
    fecha_fin: datetime
    aprobado_por_docente: bool
    feedback_docente: str | None

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    sprint_id: int
    asignado_a: int | None = None
    nombre_actividad: str = Field(..., max_length=150)
    descripcion: str
    criterios_aceptacion: str
    fecha_inicio: datetime
    fecha_fin: datetime
    tiempo_estimado_horas: int = Field(..., gt=0)
    prioridad: Prioridad = Prioridad.MEDIA
    story_points: int = Field(1, gt=0)


class TaskUpdate(BaseModel):
    """
    Schema para PUT /historia/{id}.
    Todos los campos son opcionales: solo se actualizan los que vienen
    en la petición (actualización parcial), sin sobrescribir el resto.
    """
    asignado_a: int | None = None
    nombre_actividad: str | None = Field(None, max_length=150)
    descripcion: str | None = None
    criterios_aceptacion: str | None = None
    fecha_inicio: datetime | None = None
    fecha_fin: datetime | None = None
    tiempo_estimado_horas: int | None = Field(None, gt=0)
    prioridad: Prioridad | None = None
    story_points: int | None = Field(None, gt=0)



class TaskMoveKanban(BaseModel):
    """
    Para mover una tarea en el Kanban (p.ej. a 'terminado') es OBLIGATORIO
    adjuntar evidencia o comentario -> regla validada en el servicio,
    NO solo en el frontend (principio: "las validaciones del FrontEnd
    no sustituyen a las del BackEnd").
    """
    nuevo_estado: EstadoKanban
    evidencia_url: str | None = None
    comentario: str | None = None


class TaskApprove(BaseModel):
    aprobado_por_scrum_master: bool


class TaskOut(BaseModel):
    id: int
    sprint_id: int
    asignado_a: int | None
    nombre_actividad: str
    descripcion: str
    criterios_aceptacion: str
    fecha_inicio: datetime
    fecha_fin: datetime
    tiempo_estimado_horas: int
    prioridad: Prioridad
    story_points: int
    estado_kanban: EstadoKanban
    evidencia_url: str | None
    comentario: str | None
    aprobado_por_scrum_master: bool

    model_config = ConfigDict(from_attributes=True)
