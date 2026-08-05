"""
PATRÓN DE DISEÑO: Dependency Injection (nativo de FastAPI)
-----------------------------------------------------------
FastAPI resuelve automáticamente cualquier parámetro `Depends(...)` en cada
endpoint. Aquí definimos:

- get_current_user: extrae y valida el JWT del header Authorization, y
  obtiene el usuario real desde la BD (vía UserRepository).
- require_role(*roles): fábrica de dependencias para RBAC — se usa como
  `current_user = Depends(require_role("docente", "scrum_master"))` en
  cualquier router, sin repetir lógica de autorización en cada endpoint.

Esto es exactamente lo que pide la Actividad 1 (Control de accesos estricto -
RBAC) y la Actividad 3 (Autenticación y Autorización con JWT).
"""
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas o expiradas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if payload is None or "sub" not in payload:
        raise credentials_exception

    user_repo = UserRepository(db)
    user = user_repo.get_by_id(int(payload["sub"]))
    if user is None:
        raise credentials_exception

    # Si el usuario ejerció su derecho ARCO de Cancelación, sus datos ya
    # fueron anonimizados y su sesión debe considerarse revocada. Este
    # check invalida todos los JWTs previamente emitidos SIN necesidad de
    # una blacklist externa (Redis/DB): el estado vive en la BD del user.
    if user.fecha_anonimizacion is not None:
        raise credentials_exception

    return user


def require_role(*allowed_roles: str):
    def _dependency(current_user=Depends(get_current_user)):
        if current_user.rol not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{current_user.rol}' no autorizado para esta acción.",
            )
        return current_user

    return _dependency


def verify_cron_secret(x_cron_secret: str | None = Header(default=None)):
    """
    Dependency para proteger endpoints internos disparados por jobs
    programados (GitHub Actions cron, Render Cron). Valida que el header
    X-Cron-Secret coincida con la variable de entorno CRON_SECRET.

    Se usa en lugar de JWT porque un job programado no puede autenticarse
    como un usuario real. Cumple el principio de menor privilegio: el
    secret solo permite invocar endpoints /cron/*, nada mas.
    """
    settings = get_settings()
    if not settings.cron_secret:
        # 503 en vez de 401: el servidor esta mal configurado, no es
        # culpa del cliente.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="CRON_SECRET no configurado en el servidor.",
        )
    if not x_cron_secret or x_cron_secret != settings.cron_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Cron secret invalido o ausente.",
        )
    return True
