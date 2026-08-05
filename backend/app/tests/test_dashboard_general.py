"""
Tests del endpoint GET /api/v1/dashboard/general.

Criterios de aceptacion:
1. Devuelve un arreglo con el resumen de cada equipo del curso.
2. Solo accesible para rol docente (estudiante y scrum_master reciben 403).
3. Incluye story_points_planeados y story_points_completados por equipo.
4. El porcentaje_avance se calcula correctamente.
"""
from datetime import datetime, timedelta

import pytest

from app.core.rate_limit import limiter
from app.core.security import hash_password
from app.models.sprint import Sprint
from app.models.task import Task, EstadoKanban, Prioridad
from app.models.team import Team, TeamMember
from app.models.user import User, RolUsuario

ENDPOINT = "/api/v1/dashboard/general"


# ---------------------------------------------------------------------------
# Fixture: resetea el rate limiter entre tests para evitar 429 en el login
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_limiter():
    limiter._storage.reset()
    yield
    limiter._storage.reset()



# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _crear_usuario(db, numero_control, email, rol=RolUsuario.ESTUDIANTE):
    user = User(
        nombre_completo="Test User",
        numero_control=numero_control,
        email=email,
        password_hash=hash_password("Password123"),
        rol=rol,
    )
    db.add(user)
    db.flush()
    return user


def _token_de(client, email, password="Password123"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login fallo: {r.json()}"
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _crear_equipo_con_tareas(db, user_id, nombre, grupo, tareas: list[dict]):
    """
    Crea un equipo completo con sprint y tareas.
    tareas: lista de dicts con {story_points, terminada (bool)}
    """
    team = Team(nombre_proyecto=nombre, grupo=grupo)
    db.add(team)
    db.flush()
    db.add(TeamMember(team_id=team.id, user_id=user_id, rol_scrum="Scrum Master"))

    sprint = Sprint(
        team_id=team.id,
        numero_parcial=1,
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=14),
    )
    db.add(sprint)
    db.flush()

    for t in tareas:
        estado = EstadoKanban.TERMINADO if t.get("terminada") else EstadoKanban.HACIENDO
        tarea = Task(
            sprint_id=sprint.id,
            asignado_a=user_id,
            nombre_actividad=f"Tarea {t.get('story_points')}sp",
            descripcion="Desc",
            criterios_aceptacion="Criterio",
            fecha_inicio=datetime.utcnow(),
            fecha_fin=datetime.utcnow() + timedelta(days=5),
            tiempo_estimado_horas=2,
            story_points=t.get("story_points", 1),
            estado_kanban=estado,
        )
        db.add(tarea)

    db.commit()
    return team


# ---------------------------------------------------------------------------
# Criterio 2: RBAC - solo docente puede acceder
# ---------------------------------------------------------------------------

def test_dashboard_general_requiere_rol_docente(client, db_session):
    """
    El endpoint solo debe ser accesible para rol docente.
    Un estudiante recibe 403 Forbidden.
    """
    estudiante = _crear_usuario(db_session, "80000001", "dash_est@cbtis75.edu.mx")
    db_session.commit()
    token = _token_de(client, "dash_est@cbtis75.edu.mx")

    r = client.get(ENDPOINT, headers=_headers(token))
    assert r.status_code == 403, (
        f"Un estudiante no debe acceder al dashboard general, se obtuvo {r.status_code}"
    )


def test_dashboard_general_rechaza_scrum_master(client, db_session):
    """
    El Scrum Master tampoco puede ver el dashboard general del docente.
    """
    sm = _crear_usuario(
        db_session, "80000002", "dash_sm@cbtis75.edu.mx", rol=RolUsuario.SCRUM_MASTER
    )
    db_session.commit()
    token = _token_de(client, "dash_sm@cbtis75.edu.mx")

    r = client.get(ENDPOINT, headers=_headers(token))
    assert r.status_code == 403


def test_dashboard_general_sin_token_retorna_401(client):
    """
    Sin token de autenticacion debe retornar 401.
    """
    r = client.get(ENDPOINT)
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Criterio 1 y 3: arreglo con resumen de cada equipo + story points
# ---------------------------------------------------------------------------

def test_dashboard_general_retorna_arreglo_de_equipos(client, db_session):
    """
    GET /dashboard/general devuelve una lista (arreglo) con un elemento
    por cada equipo registrado en el curso.
    """
    docente = _crear_usuario(
        db_session, "80000003", "dash_doc@cbtis75.edu.mx", rol=RolUsuario.DOCENTE
    )
    estudiante = _crear_usuario(db_session, "80000004", "dash_stu@cbtis75.edu.mx")

    # Crear 2 equipos
    _crear_equipo_con_tareas(db_session, estudiante.id, "Equipo Alpha", "A",
                             [{"story_points": 3}, {"story_points": 5, "terminada": True}])
    _crear_equipo_con_tareas(db_session, estudiante.id, "Equipo Beta", "B",
                             [{"story_points": 2}])

    token = _token_de(client, "dash_doc@cbtis75.edu.mx")
    r = client.get(ENDPOINT, headers=_headers(token))

    assert r.status_code == 200
    body = r.json()
    assert isinstance(body, list), "El response debe ser un arreglo"
    assert len(body) == 2, f"Se esperaban 2 equipos, se obtuvieron {len(body)}"


def test_dashboard_general_incluye_story_points_planeados_y_completados(client, db_session):
    """
    Criterio 3: el resumen de cada equipo incluye story_points_planeados
    y story_points_completados con los valores correctos.
    """
    docente = _crear_usuario(
        db_session, "80000005", "dash_doc2@cbtis75.edu.mx", rol=RolUsuario.DOCENTE
    )
    estudiante = _crear_usuario(db_session, "80000006", "dash_stu2@cbtis75.edu.mx")

    # Equipo con 3 tareas: 2 terminadas (5+3=8sp) y 1 pendiente (2sp)
    # Total planeado: 10sp, completado: 8sp
    team = _crear_equipo_con_tareas(
        db_session, estudiante.id, "Equipo Gamma", "G",
        [
            {"story_points": 5, "terminada": True},
            {"story_points": 3, "terminada": True},
            {"story_points": 2, "terminada": False},
        ]
    )

    token = _token_de(client, "dash_doc2@cbtis75.edu.mx")
    r = client.get(ENDPOINT, headers=_headers(token))

    assert r.status_code == 200
    equipo = next((e for e in r.json() if e["team_id"] == team.id), None)
    assert equipo is not None, f"No se encontro el equipo {team.id} en el response"

    assert equipo["story_points_planeados"] == 10, (
        f"Se esperaban 10 sp planeados, se obtuvo {equipo['story_points_planeados']}"
    )
    assert equipo["story_points_completados"] == 8, (
        f"Se esperaban 8 sp completados, se obtuvo {equipo['story_points_completados']}"
    )
    assert equipo["total_tareas"] == 3


def test_dashboard_general_calcula_porcentaje_avance(client, db_session):
    """
    El porcentaje_avance debe ser (completados / planeados) * 100.
    Para 8sp completados de 10sp planeados -> 80.0%
    """
    docente = _crear_usuario(
        db_session, "80000007", "dash_doc3@cbtis75.edu.mx", rol=RolUsuario.DOCENTE
    )
    estudiante = _crear_usuario(db_session, "80000008", "dash_stu3@cbtis75.edu.mx")

    team = _crear_equipo_con_tareas(
        db_session, estudiante.id, "Equipo Delta", "D",
        [
            {"story_points": 8, "terminada": True},
            {"story_points": 2, "terminada": False},
        ]
    )

    token = _token_de(client, "dash_doc3@cbtis75.edu.mx")
    r = client.get(ENDPOINT, headers=_headers(token))

    assert r.status_code == 200
    equipo = next(e for e in r.json() if e["team_id"] == team.id)
    assert equipo["porcentaje_avance"] == 80.0, (
        f"Se esperaba 80.0%, se obtuvo {equipo['porcentaje_avance']}"
    )


def test_dashboard_general_equipo_sin_tareas_tiene_cero_sp(client, db_session):
    """
    Un equipo sin tareas no debe causar division por cero.
    Debe retornar sp=0 y porcentaje_avance=0.0.
    """
    docente = _crear_usuario(
        db_session, "80000009", "dash_doc4@cbtis75.edu.mx", rol=RolUsuario.DOCENTE
    )
    estudiante = _crear_usuario(db_session, "80000010", "dash_stu4@cbtis75.edu.mx")

    # Equipo sin tareas
    team = _crear_equipo_con_tareas(db_session, estudiante.id, "Equipo Vacio", "V", [])

    token = _token_de(client, "dash_doc4@cbtis75.edu.mx")
    r = client.get(ENDPOINT, headers=_headers(token))

    assert r.status_code == 200
    equipo = next(e for e in r.json() if e["team_id"] == team.id)
    assert equipo["story_points_planeados"] == 0
    assert equipo["story_points_completados"] == 0
    assert equipo["porcentaje_avance"] == 0.0


def test_dashboard_general_sin_equipos_retorna_lista_vacia(client, db_session):
    """
    Si no hay equipos registrados, el endpoint debe retornar una lista vacia []
    en lugar de un error.
    """
    docente = _crear_usuario(
        db_session, "80000011", "dash_doc5@cbtis75.edu.mx", rol=RolUsuario.DOCENTE
    )
    db_session.commit()

    token = _token_de(client, "dash_doc5@cbtis75.edu.mx")
    r = client.get(ENDPOINT, headers=_headers(token))

    assert r.status_code == 200
    assert r.json() == [], f"Sin equipos debe retornar [], se obtuvo: {r.json()}"
