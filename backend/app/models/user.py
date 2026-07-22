import enum
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class RolUsuario(str, enum.Enum):
    ESTUDIANTE = "estudiante"
    SCRUM_MASTER = "scrum_master"
    DOCENTE = "docente"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    nombre_completo = Column(String(150), nullable=False)
    numero_control = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)  # NUNCA guardar texto plano (bcrypt)
    rol = Column(Enum(RolUsuario), nullable=False, default=RolUsuario.ESTUDIANTE)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Consentimiento explícito del aviso de privacidad (LFPDPPP / GDPR).
    # Guardamos la prueba de que el usuario aceptó y CUÁNDO lo hizo.
    consentimiento_privacidad = Column(Boolean, nullable=False, default=False)
    fecha_consentimiento = Column(DateTime, nullable=True)

    memberships = relationship("TeamMember", back_populates="user")
