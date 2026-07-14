from sqlalchemy.orm import Session

from app.repositories.task_repository import TaskRepository


class DashboardService:
    """
    Calcula los datos que el FrontEnd graficará: histograma de story points,
    esfuerzo por integrante, Gantt y puntos planeados vs. completados.
    El backend SOLO entrega números/JSON; el renderizado de las gráficas
    (Chart.js/Recharts/Gantt) se hace en React.
    """

    def __init__(self, db: Session):
        self.db = db
        self.task_repo = TaskRepository(db)

    def resumen_equipo(self, team_id: int) -> dict:
        tasks = self.task_repo.list_by_team(team_id)

        story_points_planeados = sum(t.story_points for t in tasks)
        story_points_completados = sum(
            t.story_points for t in tasks if t.estado_kanban.value == "terminado"
        )

        esfuerzo_por_integrante: dict[int, int] = {}
        for t in tasks:
            if t.asignado_a:
                esfuerzo_por_integrante[t.asignado_a] = (
                    esfuerzo_por_integrante.get(t.asignado_a, 0) + t.tiempo_estimado_horas
                )

        gantt = [
            {
                "id": t.id,
                "nombre": t.nombre_actividad,
                "inicio": t.fecha_inicio.isoformat(),
                "fin": t.fecha_fin.isoformat(),
                "estado": t.estado_kanban.value,
            }
            for t in tasks
        ]

        return {
            "story_points_planeados": story_points_planeados,
            "story_points_completados": story_points_completados,
            "esfuerzo_por_integrante": esfuerzo_por_integrante,
            "gantt": gantt,
            "total_tareas": len(tasks),
        }
