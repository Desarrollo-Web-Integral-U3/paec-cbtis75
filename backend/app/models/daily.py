from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Daily(Base):
    """
    Registro diario de cada integrante: qué hice ayer / qué haré hoy /
    qué me impide avanzar + acuerdos a los que llegó el equipo.
    'Módulo de Ejecución (Tablero Kanban y Dailys)'.
    """
    __tablename__ = "dailies"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    que_hice_ayer = Column(Text, nullable=False)
    que_hare_hoy = Column(Text, nullable=False)
    impedimentos = Column(Text, nullable=True)
    acuerdos = Column(Text, nullable=True)

    team = relationship("Team", back_populates="dailies")
