"""
Tests del DashboardService.

Cubre en particular el nuevo shape de esfuerzo_por_integrante
(issue #29): debe ser una lista de dicts con nombre_completo
resuelto, no un mapa {user_id: horas}.
"""
from datetime import datetime, timedelta

from app.core.security import hash_password
from app.models.sprint import Sprint
from app.models.task import Prioridad, Task
from app.models.team import Team, TeamMember
from app.models.user import RolUsuario, User
from app.services.dashboard_service import DashboardService


def _crear_escenario(db):
    """
    Escenario minimo:
    - 1 equipo con 2 integrantes (Ana y Beto).
    - 1 sprint activo.
    - 3 tareas: 2 asignadas a Ana (4h + 2h), 1 asignada a Beto (5h).
    - 1 tarea sin asignado (no debe entrar en el esfuerzo).
    Retorna el team_id.
    """
    ana = User(
        nombre_completo="Ana Ejemplo",
        numero_control="90000001",
        email="ana@test.mx",
        password_hash=hash_password("Password123"),
        rol=RolUsuario.ESTUDIANTE,
    )
    beto = User(
        nombre_completo="Beto Prueba",
        numero_control="90000002",
        email="beto@test.mx",
        password_hash=hash_password("Password123"),
        rol=RolUsuario.ESTUDIANTE,
    )
    db.add_all([ana, beto])
    db.flush()

    team = Team(nombre_proyecto="Equipo Dashboard", grupo="A")
    db.add(team)
    db.flush()

    db.add(TeamMember(team_id=team.id, user_id=ana.id, rol_scrum="Scrum Master"))
    db.add(TeamMember(team_id=team.id, user_id=beto.id, rol_scrum="Developer"))

    sprint = Sprint(
        team_id=team.id,
        numero_parcial=1,
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=14),
    )
    db.add(sprint)
    db.flush()

    base = dict(
        sprint_id=sprint.id,
        descripcion="d",
        criterios_aceptacion="c",
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=1),
        prioridad=Prioridad.MEDIA,
        story_points=3,
    )
    db.add(Task(**base, asignado_a=ana.id, nombre_actividad="T1", tiempo_estimado_horas=4))
    db.add(Task(**base, asignado_a=ana.id, nombre_actividad="T2", tiempo_estimado_horas=2))
    db.add(Task(**base, asignado_a=beto.id, nombre_actividad="T3", tiempo_estimado_horas=5))
    db.add(Task(**base, asignado_a=None, nombre_actividad="T4", tiempo_estimado_horas=99))

    db.commit()
    return team.id, ana.id, beto.id


def test_esfuerzo_devuelve_lista_con_nombre_completo(db_session):
    """
    Criterio #29: cada entrada de esfuerzo trae user_id, nombre_completo
    real (no 'Usuario N') y las horas correctas.
    """
    team_id, ana_id, beto_id = _crear_escenario(db_session)

    resumen = DashboardService(db_session).resumen_equipo(team_id)

    esfuerzo = resumen["esfuerzo_por_integrante"]
    assert isinstance(esfuerzo, list)
    assert len(esfuerzo) == 2  # tareas sin asignado no cuentan

    por_id = {e["user_id"]: e for e in esfuerzo}
    assert por_id[ana_id]["nombre_completo"] == "Ana Ejemplo"
    assert por_id[ana_id]["horas"] == 6   # 4 + 2
    assert por_id[beto_id]["nombre_completo"] == "Beto Prueba"
    assert por_id[beto_id]["horas"] == 5


def test_esfuerzo_vacio_cuando_no_hay_tareas_asignadas(db_session):
    """Sin tareas asignadas, la lista queda vacia (no crashea)."""
    team = Team(nombre_proyecto="Equipo Vacio", grupo="Z")
    db_session.add(team)
    db_session.commit()

    resumen = DashboardService(db_session).resumen_equipo(team.id)
    assert resumen["esfuerzo_por_integrante"] == []
