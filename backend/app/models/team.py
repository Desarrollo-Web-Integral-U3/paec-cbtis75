from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Team(Base):
    """
    Equipo de trabajo (2-3 integrantes) y su proyecto ABP.
    Corresponde al 'Módulo de Inicio y Gestión de Equipos'.
    """
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    nombre_proyecto = Column(String(150), nullable=False)
    descripcion_proyecto = Column(String(500), nullable=True)
    grupo = Column(String(30), nullable=True)  # p.ej. GIDS6O81-E
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    design_sprint_days = relationship(
        "DesignSprintDay", back_populates="team", cascade="all, delete-orphan"
    )
    sprints = relationship("Sprint", back_populates="team", cascade="all, delete-orphan")
    dailies = relationship("Daily", back_populates="team", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="team", cascade="all, delete-orphan")


class TeamMember(Base):
    """
    Tabla intermedia equipo <-> usuario, con el rol Scrum específico
    dentro de ESE equipo (un usuario podría ser Scrum Master en un
    proyecto y Dev en otro, aunque para este curso normalmente es 1 equipo).
    """
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rol_scrum = Column(String(50), nullable=False)  # "Scrum Master", "Dev FrontEnd", "Dev BackEnd"

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="memberships")
