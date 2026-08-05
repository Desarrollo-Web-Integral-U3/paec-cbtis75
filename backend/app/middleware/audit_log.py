"""
Middleware de Auditoria - Issue: Log de accesos

Registra por cada request entrante:
  - Metodo HTTP (GET, POST, PUT, PATCH, DELETE)
  - Ruta solicitada (path + query string si aplica)
  - user_id del usuario autenticado (o "anonimo" si el request no lleva JWT)
  - Fecha/hora UTC en formato ISO-8601

GARANTIAS DE PRIVACIDAD:
  - NUNCA se lee ni se registra el body del request.
  - NUNCA se registran contraseñas, tokens completos ni ningun dato sensible.
  - Del header Authorization solo se extrae el payload del JWT (sub -> user_id);
    el token en si NO queda en el log.
  - El nivel del logger es INFO, separado del logger raiz para poder redirigirlo
    a un destino distinto (archivo, SIEM, etc.) sin mezclar con logs de negocio.
"""
import logging
from datetime import datetime, timezone

from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import get_settings

logger = logging.getLogger("app.audit")


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Middleware Starlette/FastAPI que intercepta cada request y emite
    una linea de log de auditoria con metodo, ruta, user_id y timestamp.

    Implementa el patron Decorator sobre el ciclo request/response de ASGI:
    envuelve la llamada al siguiente handler (call_next) sin modificar
    ni inspeccionar el cuerpo de la peticion ni de la respuesta.
    """

    async def dispatch(self, request: Request, call_next):
        # --- Extraer user_id del JWT (sin leer el body) ---
        user_id = self._extraer_user_id(request)

        # --- Timestamp antes de procesar el request ---
        timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")

        # --- Delegar al siguiente handler en la cadena ASGI ---
        response = await call_next(request)

        # --- Registro de auditoria: SOLO metadatos, NUNCA body ni secrets ---
        logger.info(
            "AUDIT method=%s path=%s user_id=%s timestamp=%s status=%s",
            request.method,
            request.url.path,
            user_id,
            timestamp,
            response.status_code,
        )

        return response

    @staticmethod
    def _extraer_user_id(request: Request) -> str:
        """
        Intenta extraer el user_id (campo 'sub') del JWT en el header
        Authorization. Si el header no existe, es invalido o el token
        expiró, devuelve la cadena 'anonimo'.

        NOTA DE SEGURIDAD: solo se decodifica el payload del JWT para leer
        el 'sub'; el token completo NO se incluye en ningun log.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return "anonimo"

        token = auth_header.removeprefix("Bearer ").strip()
        try:
            settings = get_settings()
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )
            return str(payload.get("sub", "anonimo"))
        except JWTError:
            # Token invalido, expirado o mal firmado: no bloqueamos el request,
            # solo marcamos el user como anonimo en el log de auditoria.
            return "anonimo"
