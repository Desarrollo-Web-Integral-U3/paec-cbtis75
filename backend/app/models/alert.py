import enum
from datetime import datetime

from sqlalchemy import Column, Integer, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class TipoAlerta(str, enum.Enum):
    ATRASO_ENTREGA = "atraso_entrega"
    EVIDENCIA_FALTANTE = "evidencia_faltante"


class Alert(Base):
    """
    Alertas automáticas al Scrum Master.
    'Módulo de Dashboards y Alertas'.
    Generadas por app/strategies/alert_strategy.py (patrón Strategy).
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    tipo = Column(Enum(TipoAlerta), nullable=False)
    mensaje = Column(Text, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    atendida = Column(Boolean, default=False)

    team = relationship("Team", back_populates="alerts")
