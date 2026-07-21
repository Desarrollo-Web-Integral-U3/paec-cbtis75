from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Sprint(Base):
    """
    Un Sprint = un parcial. 'Módulo de Planeación (Backlog y Sprints)'.
    El profesor aprueba la planeación de cada parcial y deja retroalimentación.
    """
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    numero_parcial = Column(Integer, nullable=False)  # 1, 2, 3
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    aprobado_por_docente = Column(Boolean, default=False)
    feedback_docente = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint", cascade="all, delete-orphan")
