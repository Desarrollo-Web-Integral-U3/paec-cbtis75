"""
Servicio que notifica al Scrum Master cuando una tarea recibe una nueva
evidencia pendiente de aprobación.

Cumple el issue:
- Envía la notificación por medio del Notifier configurado (Factory).
- Deja un registro en logs para que quede evidencia de que el aviso se generó.
"""
import logging

from sqlalchemy.orm import Session

from app.factories.notification_factory import NotificationFactory
from app.models.sprint import Sprint
from app.models.task import Task
from app.models.team import TeamMember

logger = logging.getLogger(__name__)

# String exacto tal como lo guarda TeamMember.rol_scrum (mismo que usa el seed).
# Centralizado para evitar "typos" que rompan la búsqueda del Scrum Master.
ROL_SCRUM_MASTER = "Scrum Master"


def notificar_scrum_master_evidencia_nueva(db: Session, task: Task) -> bool:
    """
    Notifica al Scrum Master del equipo dueño de `task` de que hay una
    evidencia nueva pendiente de aprobación.

    Devuelve True si la notificación se envió, False si no se pudo (p.ej.
    el equipo no tiene Scrum Master registrado). En cualquier caso queda
    una entrada en logs.

    NO decide *cuándo* notificar — eso es responsabilidad del router.
    Aquí solo se encarga del "cómo": encontrar al destinatario, formatear
    el mensaje, enviar y loggear.
    """
    # Navegación: task -> sprint -> team -> TeamMember (con rol Scrum Master)
    sprint = db.query(Sprint).filter(Sprint.id == task.sprint_id).first()
    if sprint is None:
        logger.warning(
            "Task id=%s no tiene sprint asociado; no se pudo notificar.",
            task.id,
        )
        return False

    miembro_sm = (
        db.query(TeamMember)
        .filter(
            TeamMember.team_id == sprint.team_id,
            TeamMember.rol_scrum == ROL_SCRUM_MASTER,
        )
        .first()
    )
    if miembro_sm is None:
        logger.warning(
            "El equipo id=%s no tiene Scrum Master registrado; "
            "tarea id=%s no notificada.",
            sprint.team_id,
            task.id,
        )
        return False

    destinatario = miembro_sm.user.email
    mensaje = (
        f"Nueva evidencia pendiente de aprobacion en la tarea "
        f"'{task.nombre_actividad}' (id={task.id}). Revisa el tablero Kanban."
    )

    # Envío efectivo a través del Notifier configurado (consola/email/webhook).
    NotificationFactory.get_notifier().send(destinatario, mensaje)

    # Registro en logs como evidencia auditable del aviso (criterio del issue).
    logger.info(
        "Notificacion de evidencia enviada al Scrum Master %s "
        "por tarea id=%s ('%s').",
        destinatario,
        task.id,
        task.nombre_actividad,
    )
    return True
