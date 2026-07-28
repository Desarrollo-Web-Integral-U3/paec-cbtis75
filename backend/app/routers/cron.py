"""
Router para endpoints internos disparados por jobs programados.

PATRON DE SEGURIDAD: proteccion por header secret (X-Cron-Secret) en
lugar de JWT. Un GitHub Action / Render Cron no puede loguearse como un
usuario real, y hardcodear credenciales de un usuario en secrets del
repo es mala practica. En su lugar se usa un secreto opaco con alcance
limitado: solo autoriza endpoints /api/v1/cron/*, nada mas.

El secreto se comparte entre:
  - El .env del backend (variable CRON_SECRET) o la configuracion de Render.
  - Los secrets del repositorio de GitHub (CRON_SECRET).

Se rota igual que cualquier credencial: cambiando ambos valores.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import verify_cron_secret
from app.services.alert_service import AlertService

router = APIRouter(prefix="/api/v1/cron", tags=["cron"])


@router.post("/evaluar-alertas")
def evaluar_alertas_todos(
    db: Session = Depends(get_db),
    _: bool = Depends(verify_cron_secret),
):
    """
    Recorre TODOS los equipos y ejecuta las estrategias de alerta
    (Strategy Pattern en app/strategies/alert_strategy.py). Notifica al
    Scrum Master de cada equipo via el Notifier configurado.

    Se invoca automaticamente desde .github/workflows/alerts-daily.yml
    (cron diario a las 14:00 UTC / 08:00 CDMX).

    Retorna:
        {"equipos_evaluados": int, "alertas_nuevas": int}
    """
    return AlertService(db).evaluar_todos()
