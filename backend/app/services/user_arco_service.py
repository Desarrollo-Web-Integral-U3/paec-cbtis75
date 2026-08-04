"""
Servicio que aplica el derecho ARCO de Cancelación (LFPDPPP) a un usuario.

Estrategia: SOFT-DELETE con ANONIMIZACIÓN.
- NO se borra la fila de `users`: rompería FKs históricos en tasks,
  dailies y team_members. Además LFPDPPP exige poder demostrar que hubo
  consentimiento previo (consentimiento_privacidad / fecha_consentimiento
  se conservan como prueba auditable).
- SÍ se reescriben los campos PII (nombre_completo, email,
  numero_control, password_hash) a placeholders únicos por id.
- Se estampa `fecha_anonimizacion = utcnow()` como marcador de que la
  cuenta fue "cancelada", lo que también invalida cualquier JWT viejo
  (ver `core/dependencies.get_current_user`).
"""
import logging
import secrets
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User

logger = logging.getLogger(__name__)

# Placeholder que se muestra en cualquier lugar donde antes se
# renderizaba el nombre real (dashboards, tablero Kanban, etc.).
NOMBRE_PLACEHOLDER = "Usuario eliminado"


def anonimizar_usuario(db: Session, user: User) -> User:
    """
    Reescribe los campos PII del usuario y estampa fecha_anonimizacion.
    Es IDEMPOTENTE: si el usuario ya está anonimizado, no hace nada.

    Devuelve el mismo user con los campos ya modificados (útil en tests).
    """
    if user.fecha_anonimizacion is not None:
        logger.info(
            "Usuario id=%s ya estaba anonimizado; no se reprocesa.", user.id,
        )
        return user

    # Placeholders únicos por id (los campos email y numero_control son
    # UNIQUE en la BD, así que no podemos usar el mismo valor para todos).
    user.nombre_completo = NOMBRE_PLACEHOLDER
    user.email = f"eliminado+{user.id}@paec.local"
    user.numero_control = f"ELIM-{user.id}"
    # Password no reversible: cualquier intento de login queda inservible.
    # Usamos secrets.token_urlsafe para garantizar aleatoriedad criptográfica.
    user.password_hash = hash_password(secrets.token_urlsafe(32))
    user.fecha_anonimizacion = datetime.utcnow()

    db.commit()
    db.refresh(user)

    logger.info(
        "Ejercido derecho ARCO de Cancelación sobre usuario id=%s "
        "(fecha_anonimizacion=%s). FKs (tasks/dailies/team_members) preservados.",
        user.id, user.fecha_anonimizacion.isoformat(),
    )
    return user
