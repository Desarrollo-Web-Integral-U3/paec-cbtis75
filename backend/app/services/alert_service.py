from sqlalchemy.orm import Session

from app.factories.notification_factory import NotificationFactory
from app.models.alert import Alert
from app.models.team import Team, TeamMember
from app.strategies.alert_strategy import ALERT_STRATEGIES


class AlertService:
    """
    Recorre todas las AlertStrategy registradas, guarda las alertas nuevas
    en BD y notifica al Scrum Master del equipo usando el Notifier que
    entregue NotificationFactory (email, webhook o consola, según .env).
    """

    def __init__(self, db: Session):
        self.db = db
        self.notifier = NotificationFactory.get_notifier()

    def _get_scrum_master_email(self, team_id: int) -> str | None:
        member = (
            self.db.query(TeamMember)
            .filter(TeamMember.team_id == team_id, TeamMember.rol_scrum == "Scrum Master")
            .first()
        )
        return member.user.email if member else None

    def evaluar_equipo(self, team_id: int) -> list[Alert]:
        nuevas_alertas: list[Alert] = []

        for strategy in ALERT_STRATEGIES:
            mensajes = strategy.detectar(self.db, team_id)
            for mensaje in mensajes:
                alerta = Alert(team_id=team_id, tipo=strategy.tipo, mensaje=mensaje)
                self.db.add(alerta)
                nuevas_alertas.append(alerta)

        if nuevas_alertas:
            self.db.commit()
            destinatario = self._get_scrum_master_email(team_id) or "scrum_master_no_definido"
            for alerta in nuevas_alertas:
                self.notifier.send(destinatario, alerta.mensaje)

        return nuevas_alertas

    def evaluar_todos(self) -> dict:
        """
        Ejecuta la evaluacion de alertas para TODOS los equipos registrados.
        Diseñado para jobs programados (GitHub Actions cron, Render Cron)
        que no reciben un team_id especifico. Retorna un resumen con el
        conteo de equipos evaluados y alertas nuevas creadas.
        """
        teams = self.db.query(Team).all()
        total_alertas = 0
        for team in teams:
            nuevas = self.evaluar_equipo(team.id)
            total_alertas += len(nuevas)
        return {
            "equipos_evaluados": len(teams),
            "alertas_nuevas": total_alertas,
        }
