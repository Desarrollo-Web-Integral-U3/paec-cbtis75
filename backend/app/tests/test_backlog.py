"""
Tests del Issue Backlog: PUT y DELETE para historias de usuario.

Criterios de aceptacion:
- PUT actualiza unicamente los campos enviados (partial update).
- DELETE elimina la historia correctamente.
- Ambos devuelven 404 si el id no existe.
"""
from datetime import datetime, timedelta

from app.models.user import User, RolUsuario
from app.models.task import Task, Prioridad, EstadoKanban
from app.models.sprint import Sprint
from app.models.team import Team, TeamMember
from app.core.security import hash_password


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


def _crear_equipo_sprint_historia(db, user_id):
    """Crea equipo -> sprint -> historia en BD y devuelve la historia."""
    team = Team(nombre_proyecto="Equipo Backlog", grupo="A")
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

    historia = Task(
        sprint_id=sprint.id,
        asignado_a=user_id,
        nombre_actividad="Historia original",
        descripcion="Descripcion original",
        criterios_aceptacion="Criterio original",
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=7),
        tiempo_estimado_horas=4,
        prioridad=Prioridad.MEDIA,
        story_points=3,
    )
    db.add(historia)
    db.commit()
    db.refresh(historia)
    return historia


# ---------------------------------------------------------------------------
# Tests PUT /api/v1/historia/{id}
# ---------------------------------------------------------------------------

def test_put_historia_actualiza_campos_enviados(client, db_session):
    """
    Criterio #1: PUT actualiza unicamente los campos enviados.
    El resto de campos mantiene su valor original.
    """
    user = _crear_usuario(db_session, "40000001", "put_test1@cbtis75.edu.mx")
    historia = _crear_equipo_sprint_historia(db_session, user.id)
    token = _token_de(client, "put_test1@cbtis75.edu.mx")

    r = client.put(
        f"/api/v1/historia/{historia.id}",
        json={"nombre_actividad": "Historia actualizada", "prioridad": "alta"},
        headers=_headers(token),
    )

    assert r.status_code == 200
    body = r.json()
    # Campos actualizados
    assert body["nombre_actividad"] == "Historia actualizada"
    assert body["prioridad"] == "alta"
    # Campos NO enviados -> mantienen valor original
    assert body["descripcion"] == "Descripcion original"
    assert body["criterios_aceptacion"] == "Criterio original"
    assert body["story_points"] == 3
    assert body["tiempo_estimado_horas"] == 4


def test_put_historia_actualiza_solo_un_campo(client, db_session):
    """
    Enviar un solo campo en PUT no debe afectar los demas.
    """
    user = _crear_usuario(db_session, "40000002", "put_test2@cbtis75.edu.mx")
    historia = _crear_equipo_sprint_historia(db_session, user.id)
    token = _token_de(client, "put_test2@cbtis75.edu.mx")

    r = client.put(
        f"/api/v1/historia/{historia.id}",
        json={"story_points": 8},
        headers=_headers(token),
    )

    assert r.status_code == 200
    body = r.json()
    assert body["story_points"] == 8
    # El resto no cambia
    assert body["nombre_actividad"] == "Historia original"
    assert body["prioridad"] == "media"


def test_put_historia_inexistente_retorna_404(client, db_session):
    """
    Criterio #3: PUT con id que no existe devuelve 404.
    """
    user = _crear_usuario(db_session, "40000003", "put_test3@cbtis75.edu.mx")
    db_session.commit()
    token = _token_de(client, "put_test3@cbtis75.edu.mx")

    r = client.put(
        "/api/v1/historia/999999",
        json={"nombre_actividad": "No existe"},
        headers=_headers(token),
    )

    assert r.status_code == 404
    assert "no encontrada" in r.json()["detail"].lower()


def test_put_historia_sin_token_retorna_401(client, db_session):
    """
    PUT sin autenticacion debe retornar 401.
    """
    user = _crear_usuario(db_session, "40000004", "put_test4@cbtis75.edu.mx")
    historia = _crear_equipo_sprint_historia(db_session, user.id)

    r = client.put(
        f"/api/v1/historia/{historia.id}",
        json={"nombre_actividad": "Sin token"},
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Tests DELETE /api/v1/historia/{id}
# ---------------------------------------------------------------------------

def test_delete_historia_elimina_correctamente(client, db_session):
    """
    Criterio #2: DELETE elimina la historia y retorna 204 sin body.
    """
    user = _crear_usuario(db_session, "40000005", "del_test1@cbtis75.edu.mx")
    historia = _crear_equipo_sprint_historia(db_session, user.id)
    historia_id = historia.id
    token = _token_de(client, "del_test1@cbtis75.edu.mx")

    r = client.delete(
        f"/api/v1/historia/{historia_id}",
        headers=_headers(token),
    )

    assert r.status_code == 204
    assert r.content == b""   # 204 No Content: sin body

    # Verificar que ya no existe en BD
    eliminada = db_session.query(Task).filter(Task.id == historia_id).first()
    assert eliminada is None, "La historia aun existe en BD tras el DELETE"


def test_delete_historia_inexistente_retorna_404(client, db_session):
    """
    Criterio #3: DELETE con id que no existe devuelve 404.
    """
    user = _crear_usuario(db_session, "40000006", "del_test2@cbtis75.edu.mx")
    db_session.commit()
    token = _token_de(client, "del_test2@cbtis75.edu.mx")

    r = client.delete(
        "/api/v1/historia/999999",
        headers=_headers(token),
    )

    assert r.status_code == 404
    assert "no encontrada" in r.json()["detail"].lower()


def test_delete_historia_sin_token_retorna_401(client, db_session):
    """
    DELETE sin autenticacion debe retornar 401.
    """
    user = _crear_usuario(db_session, "40000007", "del_test3@cbtis75.edu.mx")
    historia = _crear_equipo_sprint_historia(db_session, user.id)

    r = client.delete(f"/api/v1/historia/{historia.id}")
    assert r.status_code == 401


def test_delete_no_afecta_otras_historias(client, db_session):
    """
    Eliminar una historia no debe eliminar otras del mismo sprint.
    """
    user = _crear_usuario(db_session, "40000008", "del_test4@cbtis75.edu.mx")
    historia1 = _crear_equipo_sprint_historia(db_session, user.id)
    # Crear segunda historia en el mismo sprint
    historia2 = Task(
        sprint_id=historia1.sprint_id,
        asignado_a=user.id,
        nombre_actividad="Historia 2",
        descripcion="Desc 2",
        criterios_aceptacion="Criterio 2",
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=5),
        tiempo_estimado_horas=2,
        story_points=1,
    )
    db_session.add(historia2)
    db_session.commit()
    db_session.refresh(historia2)

    token = _token_de(client, "del_test4@cbtis75.edu.mx")

    # Eliminar solo la primera
    r = client.delete(f"/api/v1/historia/{historia1.id}", headers=_headers(token))
    assert r.status_code == 204

    # La segunda sigue en BD
    sobreviviente = db_session.query(Task).filter(Task.id == historia2.id).first()
    assert sobreviviente is not None, "DELETE elimino mas historias de las esperadas"


# ---------------------------------------------------------------------------
# Tests validador de fechas en POST /api/v1/historia
# ---------------------------------------------------------------------------

def test_crear_historia_fecha_fin_anterior_a_inicio_devuelve_422(client, db_session):
    """
    Criterio: al crear una historia con fecha_fin < fecha_inicio, el endpoint
    debe rechazar con 422 y un mensaje claro que indique el problema.

    El validator vive en el schema TaskCreate (@model_validator) — arroja
    ValueError que FastAPI convierte automáticamente a 422 con detail.msg
    que incluye el mensaje del ValueError.
    """
    # Preparar un usuario, equipo y sprint para tener un sprint_id válido
    user = _crear_usuario(db_session, "50000001", "fechas_test@cbtis75.edu.mx")
    team = Team(nombre_proyecto="Equipo Fechas", grupo="B")
    db_session.add(team)
    db_session.flush()
    db_session.add(TeamMember(team_id=team.id, user_id=user.id, rol_scrum="Scrum Master"))
    sprint = Sprint(
        team_id=team.id,
        numero_parcial=1,
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=14),
    )
    db_session.add(sprint)
    db_session.commit()
    db_session.refresh(sprint)

    token = _token_de(client, "fechas_test@cbtis75.edu.mx")

    # Payload inválido: fecha_fin ANTES que fecha_inicio
    ahora = datetime.utcnow()
    payload = {
        "sprint_id": sprint.id,
        "nombre_actividad": "Historia con fechas invertidas",
        "descripcion": "Descripcion",
        "criterios_aceptacion": "Criterio",
        "fecha_inicio": (ahora + timedelta(days=5)).isoformat(),
        "fecha_fin": ahora.isoformat(),  # anterior a fecha_inicio -> DEBE fallar
        "tiempo_estimado_horas": 4,
        "story_points": 3,
    }

    r = client.post("/api/v1/historia", json=payload, headers=_headers(token))

    assert r.status_code == 422, f"Se esperaba 422 pero llegó {r.status_code}: {r.text}"

    # El mensaje debe ser CLARO: menciona los dos campos involucrados.
    # Pydantic devuelve el detail como lista de objetos con 'msg'.
    detail = r.json()["detail"]
    mensajes = " ".join(err["msg"].lower() for err in detail)
    assert "fecha_fin" in mensajes
    assert "fecha_inicio" in mensajes
