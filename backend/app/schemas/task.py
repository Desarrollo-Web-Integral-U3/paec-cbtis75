from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.task import EstadoKanban, Prioridad


# Mensaje único para el error de rango de fechas. Centralizado para que
# schemas, router y tests hablen el mismo idioma.
MSG_FECHAS_INVALIDAS = "fecha_fin no puede ser anterior a fecha_inicio."


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


class SprintApprovalUpdate(BaseModel):
    feedback_docente: str | None = None


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

    @model_validator(mode="after")
    def _fecha_fin_no_anterior_a_inicio(self):
        # Corre DESPUES de que Pydantic parseó fecha_inicio y fecha_fin como
        # datetime. Si el rango es inválido, arrojamos ValueError y FastAPI
        # convierte automáticamente el error a HTTP 422.
        # Aquí ambas fechas son requeridas -> siempre se ejecuta la comparación.
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError(MSG_FECHAS_INVALIDAS)
        return self


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

    @model_validator(mode="after")
    def _fecha_fin_no_anterior_a_inicio(self):
        # Solo validamos si el cliente mandó AMBAS fechas en la misma
        # petición. Si mandó solo una, no hay con qué comparar a nivel de
        # schema (habría que ir a BD -> responsabilidad del router).
        if self.fecha_inicio is not None and self.fecha_fin is not None:
            if self.fecha_fin < self.fecha_inicio:
                raise ValueError(MSG_FECHAS_INVALIDAS)
        return self


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
