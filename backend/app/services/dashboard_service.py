from sqlalchemy.orm import Session

from app.models.team import Team
from app.models.user import User
from app.repositories.task_repository import TaskRepository


class DashboardService:
    """
    Calcula los datos que el FrontEnd graficara: histograma de story points,
    esfuerzo por integrante, Gantt y puntos planeados vs. completados.
    El backend SOLO entrega numeros/JSON; el renderizado de las graficas
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

        # Suma total de horas asignadas por integrante (por user_id).
        # Solo se cuentan tareas con asignado_a definido.
        horas_por_user_id: dict[int, int] = {}
        for t in tasks:
            if t.asignado_a:
                horas_por_user_id[t.asignado_a] = (
                    horas_por_user_id.get(t.asignado_a, 0) + t.tiempo_estimado_horas
                )

        # Resolver user_id -> nombre_completo con UNA sola query (in_())
        # para evitar N+1 selects. El resultado es una lista de dicts para
        # que el frontend pueda mapear directo a las barras del chart sin
        # tener que hacer un join adicional contra otro endpoint.
        esfuerzo_por_integrante: list[dict] = []
        if horas_por_user_id:
            usuarios = (
                self.db.query(User)
                .filter(User.id.in_(horas_por_user_id.keys()))
                .all()
            )
            nombre_por_id = {u.id: u.nombre_completo for u in usuarios}
            for user_id, horas in horas_por_user_id.items():
                esfuerzo_por_integrante.append({
                    "user_id": user_id,
                    "nombre_completo": nombre_por_id.get(user_id, f"Usuario {user_id}"),
                    "horas": horas,
                })

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

    def resumen_general(self) -> list[dict]:
        """
        Devuelve el resumen de avance de TODOS los equipos del curso.
        Usado por GET /api/v1/dashboard/general (solo docente).

        Por cada equipo incluye:
        - story_points_planeados: suma de story_points de todas sus tareas.
        - story_points_completados: suma de story_points de tareas en estado 'terminado'.
        - porcentaje_avance: (completados / planeados) * 100, o 0.0 si no hay tareas.
        - total_tareas: numero de historias registradas.

        Carga todos los equipos en una sola query y reutiliza list_by_team()
        para el calculo de cada equipo.
        """
        equipos = self.db.query(Team).order_by(Team.id.asc()).all()
        resultado = []

        for equipo in equipos:
            tasks = self.task_repo.list_by_team(equipo.id)

            planeados = sum(t.story_points for t in tasks)
            completados = sum(
                t.story_points for t in tasks if t.estado_kanban.value == "terminado"
            )
            porcentaje = round((completados / planeados) * 100, 1) if planeados > 0 else 0.0

            resultado.append({
                "team_id": equipo.id,
                "nombre_proyecto": equipo.nombre_proyecto,
                "grupo": equipo.grupo,
                "total_tareas": len(tasks),
                "story_points_planeados": planeados,
                "story_points_completados": completados,
                "porcentaje_avance": porcentaje,
            })

        return resultado
