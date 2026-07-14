from datetime import datetime

from sqlalchemy.orm import Session

from app.models.task import Task, EstadoKanban
from app.repositories.base_repository import BaseRepository


class TaskRepository(BaseRepository[Task]):
    def __init__(self, db: Session):
        super().__init__(db, Task)

    def list_by_sprint(self, sprint_id: int) -> list[Task]:
        return self.db.query(Task).filter(Task.sprint_id == sprint_id).all()

    def list_by_team(self, team_id: int) -> list[Task]:
        # join implícito vía Sprint.team_id
        from app.models.sprint import Sprint
        return (
            self.db.query(Task)
            .join(Sprint, Task.sprint_id == Sprint.id)
            .filter(Sprint.team_id == team_id)
            .all()
        )

    def list_overdue_incomplete(self, team_id: int) -> list[Task]:
        """Tareas vencidas y aún no terminadas -> usado por AlertStrategy."""
        from app.models.sprint import Sprint
        return (
            self.db.query(Task)
            .join(Sprint, Task.sprint_id == Sprint.id)
            .filter(
                Sprint.team_id == team_id,
                Task.fecha_fin < datetime.utcnow(),
                Task.estado_kanban != EstadoKanban.TERMINADO,
            )
            .all()
        )
