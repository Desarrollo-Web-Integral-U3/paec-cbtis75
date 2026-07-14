"""
PATRÓN DE DISEÑO: Strategy
-----------------------------
Cada "razón" por la que se debe alertar al Scrum Master es una estrategia
intercambiable. Hoy tenemos dos (atraso en entregas, evidencia faltante),
pero se pueden agregar más SIN modificar AlertService: solo se agrega una
clase nueva que implemente AlertStrategy y se registra en la lista.
"""
from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.models.alert import TipoAlerta
from app.repositories.task_repository import TaskRepository


class AlertStrategy(ABC):
    tipo: TipoAlerta

    @abstractmethod
    def detectar(self, db: Session, team_id: int) -> list[str]:
        """Devuelve una lista de mensajes de alerta a generar (puede ser vacía)."""
        ...


class AtrasoEntregaStrategy(AlertStrategy):
    tipo = TipoAlerta.ATRASO_ENTREGA

    def detectar(self, db: Session, team_id: int) -> list[str]:
        repo = TaskRepository(db)
        vencidas = repo.list_overdue_incomplete(team_id)
        return [
            f"La tarea '{t.nombre_actividad}' venció el {t.fecha_fin:%Y-%m-%d} "
            f"y sigue en estado '{t.estado_kanban.value}'."
            for t in vencidas
        ]


class EvidenciaFaltanteStrategy(AlertStrategy):
    tipo = TipoAlerta.EVIDENCIA_FALTANTE

    def detectar(self, db: Session, team_id: int) -> list[str]:
        repo = TaskRepository(db)
        tareas = repo.list_by_team(team_id)
        sin_evidencia = [
            t for t in tareas
            if t.estado_kanban.value != "por_hacer" and not t.evidencia_url
        ]
        return [
            f"La tarea '{t.nombre_actividad}' está '{t.estado_kanban.value}' "
            f"pero no tiene evidencia adjunta."
            for t in sin_evidencia
        ]


# Registro de estrategias activas (fácil de extender)
ALERT_STRATEGIES: list[AlertStrategy] = [
    AtrasoEntregaStrategy(),
    EvidenciaFaltanteStrategy(),
]
