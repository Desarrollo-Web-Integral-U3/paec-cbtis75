"""
PATRÓN DE DISEÑO: Factory
----------------------------
NotificationFactory decide, según app.core.config.Settings.notification_provider,
QUÉ implementación concreta de notificador se debe instanciar (consola,
email vía API externa, o webhook) SIN que el resto del código (AlertService)
necesite saber cuál se está usando. Así es como cumplimos con:

  "Web Services de Terceros: la aplicación debe consumir al menos una API
  externa... Gestión de Proyectos PAEC puede integrar una API de
  notificaciones o de calendario para alertar al Scrum Master sobre retrasos."

Para producción, EmailNotifier llama a una API real (p.ej. Resend, SendGrid,
o el servicio de correo institucional). Aquí se deja el esqueleto listo:
solo hace falta poner la URL/API key reales en el .env.
"""
from abc import ABC, abstractmethod

import httpx

from app.core.config import get_settings


class Notifier(ABC):
    @abstractmethod
    def send(self, destinatario: str, mensaje: str) -> None:
        ...


class ConsoleNotifier(Notifier):
    """Fallback usado en desarrollo: solo imprime en consola/logs."""
    def send(self, destinatario: str, mensaje: str) -> None:
        print(f"[NOTIFICACION -> {destinatario}] {mensaje}")


class EmailNotifier(Notifier):
    """Notificador real vía API externa de correo (Resend/SendGrid/etc.)."""
    def __init__(self):
        settings = get_settings()
        self.api_url = settings.email_api_url
        self.api_key = settings.email_api_key

    def send(self, destinatario: str, mensaje: str) -> None:
        if not self.api_url or not self.api_key:
            print(f"[EmailNotifier] Falta configurar email_api_url/email_api_key. "
                  f"Mensaje no enviado a {destinatario}: {mensaje}")
            return
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"to": destinatario, "subject": "Alerta PAEC", "text": mensaje}
        with httpx.Client(timeout=10) as client:
            client.post(self.api_url, json=payload, headers=headers)


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
