import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class EstadoKanban(str, enum.Enum):
    POR_HACER = "por_hacer"
    HACIENDO = "haciendo"
    TERMINADO = "terminado"


class Prioridad(str, enum.Enum):
    ALTA = "alta"
    MEDIA = "media"
    BAJA = "baja"


class Task(Base):
    """
    Historia de usuario / actividad del backlog.
    Cubre TODOS los campos que pide explícitamente la rúbrica:
    nombre, descripción, criterios de aceptación, asignado, fechas,
    tiempo estimado, sprint al que pertenece y prioridad — más lo
    necesario para Kanban, evidencias y story points (dashboards).
    """
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    sprint_id = Column(Integer, ForeignKey("sprints.id"), nullable=False)
    asignado_a = Column(Integer, ForeignKey("users.id"), nullable=True)

    nombre_actividad = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=False)
    criterios_aceptacion = Column(Text, nullable=False)

    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    tiempo_estimado_horas = Column(Integer, nullable=False)
    prioridad = Column(Enum(Prioridad), nullable=False, default=Prioridad.MEDIA)
    story_points = Column(Integer, nullable=False, default=1)  # para histogramas/dashboards

    estado_kanban = Column(Enum(EstadoKanban), nullable=False, default=EstadoKanban.POR_HACER)
    evidencia_url = Column(String(500), nullable=True)
    evidencia_public_id = Column(String(200), nullable=True)   # ID interno de Cloudinary
    comentario = Column(Text, nullable=True)
    # Para mover a "Terminado" es obligatorio subir evidencia Y que el Scrum Master
    # la apruebe (regla de negocio validada en el servicio, no solo en el front).
    aprobado_por_scrum_master = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    sprint = relationship("Sprint", back_populates="tasks")
