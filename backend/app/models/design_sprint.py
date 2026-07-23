import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class DiaDesignSprint(str, enum.Enum):
    MAPEAR = "mapear"          # lunes
    BOCETAR = "bocetar"        # martes
    DECIDIR = "decidir"        # miércoles
    PROTOTIPAR = "prototipar"  # jueves
    PROBAR = "probar"          # viernes


class DesignSprintDay(Base):
    """
    Un registro por cada uno de los 5 días del Design Sprint de Google,
    por equipo. 'Módulo de Ideación (Google Design Sprint)'.
    """
    __tablename__ = "design_sprint_days"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    dia = Column(Enum(DiaDesignSprint), nullable=False)
    fecha_planeada = Column(DateTime, nullable=True)
    plan_descripcion = Column(Text, nullable=True)       # qué van a hacer ese día
    evidencia_url = Column(String(500), nullable=True)         # URL publica devuelta por Cloudinary
    evidencia_public_id = Column(String(200), nullable=True)   # ID interno para borrar/reemplazar
    comentario_docente = Column(Text, nullable=True)
    completado = Column(Integer, default=0)  # 0/1 como boolean simple

    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="design_sprint_days")
