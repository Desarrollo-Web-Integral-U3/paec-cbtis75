"""
Script CLI para verificar rápidamente el envío de correos con el proveedor
configurado (Resend o el que sea).

Uso:
    docker compose exec backend python -m app.scripts.probar_email TU_CORREO@ejemplo.com

Manda UN correo de prueba y sale. Sirve como evidencia manual del criterio
del issue "una alerta generada llega realmente al correo del Scrum Master"
sin necesidad de disparar todo el flujo de Kanban/alertas.

Si el correo no llega:
    - Revisa la carpeta de Spam / Promociones.
    - Verifica los logs del backend:  docker compose logs backend --tail=30
    - Confirma que NOTIFICATION_PROVIDER=email y EMAIL_API_KEY estén en .env.
"""
import logging
import sys

from app.factories.notification_factory import NotificationFactory


# Configura el logger para que veamos los INFO/ERROR del EmailNotifier
# aunque este script se corra fuera del contexto de FastAPI.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


def main() -> int:
    if len(sys.argv) != 2:
        print("Uso: python -m app.scripts.probar_email destinatario@ejemplo.com")
        return 1

    destinatario = sys.argv[1].strip()
    notifier = NotificationFactory.get_notifier()

    mensaje = (
        "Correo de prueba desde el sistema PAEC. "
        "Si estás leyendo esto, la integración con el proveedor real de "
        "correo funciona correctamente y las alertas al Scrum Master "
        "empezarán a llegar automáticamente."
    )

    print(f"Enviando correo de prueba a {destinatario}...")
    print(f"Notifier activo: {type(notifier).__name__}")
    notifier.send(destinatario, mensaje)
    print("Listo. Revisa tu bandeja de entrada (y Spam por si acaso).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
