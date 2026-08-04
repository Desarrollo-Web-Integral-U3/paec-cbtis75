"""
PATRÓN DE DISEÑO: Factory
----------------------------
NotificationFactory decide, según app.core.config.Settings.notification_provider,
QUÉ implementación concreta de notificador se debe instanciar (consola,
email vía API externa, o webhook) SIN que el resto del código (AlertService,
evidence_notification_service, etc.) necesite saber cuál se está usando.

EmailNotifier consume la API real de Resend (https://resend.com).
Configuración: variables EMAIL_API_KEY, EMAIL_API_URL y EMAIL_FROM en .env.
Ver docs/EMAIL_INTEGRATION.md para el paso a paso.
"""
import logging
from abc import ABC, abstractmethod

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class Notifier(ABC):
    @abstractmethod
    def send(self, destinatario: str, mensaje: str) -> None:
        ...


class ConsoleNotifier(Notifier):
    """Fallback usado en desarrollo: solo imprime en consola/logs."""
    def send(self, destinatario: str, mensaje: str) -> None:
        print(f"[NOTIFICACION -> {destinatario}] {mensaje}")


class EmailNotifier(Notifier):
    """
    Notificador real vía la API de Resend.

    - Endpoint: POST https://api.resend.com/emails
    - Auth: Authorization: Bearer <API_KEY>
    - Payload mínimo: {"from": ..., "to": [...], "subject": ..., "text": ...}

    Diseño defensivo:
    - Si fallan las credenciales, se loguea y NO se hace la request
      (evita mandar mails con key incompleta durante desarrollo).
    - Si Resend devuelve error 4xx/5xx, se loguea con el body pero NO
      se propaga la excepción: una caída del proveedor no debe tumbar
      el request principal (subir evidencia, aprobar sprint, etc.).
    - En éxito, se loguea el `id` que devuelve Resend para poder
      rastrear el correo desde su dashboard.
    """

    def __init__(self):
        settings = get_settings()
        self.api_url = settings.email_api_url
        self.api_key = settings.email_api_key
        self.email_from = settings.email_from

    @staticmethod
    def _derivar_asunto(mensaje: str) -> str:
        """
        Asunto dinámico a partir del mensaje: primera oración o primeros 80
        caracteres, siempre con el prefijo "PAEC:" para que sea reconocible
        en la bandeja del Scrum Master.

        Vive AQUÍ (dentro del notifier) en vez de exigir asunto explícito a
        cada caller — así no rompemos la interfaz Notifier.send(destinatario,
        mensaje) que ya usan AlertService y evidence_notification_service.
        """
        primera_oracion = mensaje.split(".")[0].strip()
        if len(primera_oracion) > 80:
            primera_oracion = primera_oracion[:77].rstrip() + "..."
        return f"PAEC: {primera_oracion}"

    def send(self, destinatario: str, mensaje: str) -> None:
        if not self.api_url or not self.api_key:
            logger.warning(
                "EmailNotifier sin credenciales; correo no enviado a %s. "
                "Configura EMAIL_API_KEY y EMAIL_API_URL en .env.",
                destinatario,
            )
            return

        asunto = self._derivar_asunto(mensaje)
        payload = {
            "from": self.email_from,
            "to": [destinatario],
            "subject": asunto,
            "text": mensaje,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            with httpx.Client(timeout=10) as client:
                r = client.post(self.api_url, json=payload, headers=headers)
        except httpx.HTTPError as exc:
            logger.error(
                "Fallo de red al enviar correo a %s vía %s: %s",
                destinatario, self.api_url, exc,
            )
            return

        if r.status_code >= 400:
            # Log completo del body para poder depurar (Resend suele
            # devolver {"name": "...", "message": "..."} en errores).
            logger.error(
                "Resend rechazó el envío a %s (status=%s): %s",
                destinatario, r.status_code, r.text,
            )
            return

        # Éxito: guardar el id del correo por si hay que rastrearlo en Resend.
        try:
            email_id = r.json().get("id", "<sin-id>")
        except ValueError:
            email_id = "<respuesta-no-json>"
        logger.info(
            "Correo enviado a %s vía Resend (id=%s, asunto='%s').",
            destinatario, email_id, asunto,
        )


class WebhookNotifier(Notifier):
    """Alternativa: enviar la alerta a un webhook (p.ej. Discord/Slack)."""
    def __init__(self):
        settings = get_settings()
        self.webhook_url = settings.email_api_url  # reutilizamos el campo de URL

    def send(self, destinatario: str, mensaje: str) -> None:
        if not self.webhook_url:
            print(f"[WebhookNotifier] Falta configurar webhook_url. Mensaje: {mensaje}")
            return
        with httpx.Client(timeout=10) as client:
            client.post(self.webhook_url, json={"content": f"@{destinatario}: {mensaje}"})


class NotificationFactory:
    @staticmethod
    def get_notifier() -> Notifier:
        provider = get_settings().notification_provider
        if provider == "email":
            return EmailNotifier()
        if provider == "webhook":
            return WebhookNotifier()
        return ConsoleNotifier()
