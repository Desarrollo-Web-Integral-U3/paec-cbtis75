"""
Tests del Issue #8: auto-creacion de los 5 dias del Design Sprint.

Criterio de aceptacion:
- Al hacer POST /equipo/ se crean automaticamente mapear, bocetar,
  decidir, prototipar y probar, sin crearlos manualmente.
- Cada registro queda asociado al equipo recien creado.
- Los dias aparecen en la respuesta del POST (design_sprint_days).
"""
from app.models.design_sprint import DesignSprintDay, DiaDesignSprint
from app.models.user import User, RolUsuario
from app.core.security import hash_password


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

DIAS_ESPERADOS = [
    DiaDesignSprint.MAPEAR,
    DiaDesignSprint.BOCETAR,
    DiaDesignSprint.DECIDIR,
    DiaDesignSprint.PROTOTIPAR,
    DiaDesignSprint.PROBAR,
]


def _crear_usuario(db_session, numero_control: str, email: str) -> User:
    """Crea un usuario estudiante directamente en BD y lo devuelve."""
    user = User(
        nombre_completo="Estudiante Test",
        numero_control=numero_control,
        email=email,
        password_hash=hash_password("Password123"),
        rol=RolUsuario.ESTUDIANTE,
    )
    db_session.add(user)
    db_session.flush()
    return user


def _token_de(client, email: str, password: str = "Password123") -> str:
    """Hace login y devuelve el Bearer token."""
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert r.status_code == 200, f"Login fallo: {r.json()}"
    return r.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_crear_equipo_genera_exactamente_5_dias_design_sprint(client, db_session):
    """
    Criterio de aceptacion #8-1:
    Al hacer POST /equipo/ se crean automaticamente los 5 dias del
    Design Sprint sin que el usuario los cree manualmente.
    """
    user = _crear_usuario(db_session, "30000001", "miembro1@cbtis75.edu.mx")
    db_session.commit()
    token = _token_de(client, "miembro1@cbtis75.edu.mx")

    r = client.post(
        "/api/v1/equipo/",
        json={
            "nombre_proyecto": "Proyecto Sprint Test",
            "descripcion_proyecto": "Descripcion de prueba",
            "grupo": "GIDS6O81-E",
            "members": [{"user_id": user.id, "rol_scrum": "Scrum Master"}],
        },
        headers=_headers(token),
    )

    assert r.status_code == 201
    body = r.json()

    assert "design_sprint_days" in body, "La respuesta debe incluir design_sprint_days"
    dias = body["design_sprint_days"]
    assert len(dias) == 5, f"Se esperaban 5 dias, se obtuvieron {len(dias)}"


def test_crear_equipo_genera_los_5_dias_en_orden_correcto(client, db_session):
    """
    Los dias deben generarse en el orden: mapear, bocetar, decidir,
    prototipar, probar — el orden del enum DiaDesignSprint.
    """
    user = _crear_usuario(db_session, "30000002", "miembro2@cbtis75.edu.mx")
    db_session.commit()
    token = _token_de(client, "miembro2@cbtis75.edu.mx")

    r = client.post(
        "/api/v1/equipo/",
        json={
            "nombre_proyecto": "Proyecto Orden Sprint",
            "members": [{"user_id": user.id, "rol_scrum": "Dev FrontEnd"}],
        },
        headers=_headers(token),
    )

    assert r.status_code == 201
    dias = r.json()["design_sprint_days"]

    nombres_obtenidos = [d["dia"] for d in dias]
    nombres_esperados = [d.value for d in DIAS_ESPERADOS]
    assert nombres_obtenidos == nombres_esperados, (
        f"Orden incorrecto.\nEsperado: {nombres_esperados}\nObtenido: {nombres_obtenidos}"
    )


def test_dias_design_sprint_quedan_asociados_al_equipo_correcto(client, db_session):
    """
    Cada DesignSprintDay creado debe tener team_id = el equipo recien creado.
    Se verifica directamente en la BD, no solo en la respuesta JSON.
    """
    user = _crear_usuario(db_session, "30000003", "miembro3@cbtis75.edu.mx")
    db_session.commit()
    token = _token_de(client, "miembro3@cbtis75.edu.mx")

    r = client.post(
        "/api/v1/equipo/",
        json={
            "nombre_proyecto": "Proyecto Integridad",
            "members": [{"user_id": user.id, "rol_scrum": "Dev BackEnd"}],
        },
        headers=_headers(token),
    )

    assert r.status_code == 201
    team_id = r.json()["id"]

    dias_en_bd = (
        db_session.query(DesignSprintDay)
        .filter(DesignSprintDay.team_id == team_id)
        .all()
    )
    assert len(dias_en_bd) == 5
    for dia in dias_en_bd:
        assert dia.team_id == team_id
        assert dia.completado == 0
        assert dia.evidencia_url is None
        assert dia.plan_descripcion is None


def test_dias_iniciales_estan_vacios_listos_para_captura(client, db_session):
    """
    Los dias auto-creados deben estar vacios (sin plan ni evidencia),
    listos para que el equipo los rellene progresivamente.
    """
    user = _crear_usuario(db_session, "30000004", "miembro4@cbtis75.edu.mx")
    db_session.commit()
    token = _token_de(client, "miembro4@cbtis75.edu.mx")

    r = client.post(
        "/api/v1/equipo/",
        json={
            "nombre_proyecto": "Proyecto Vacio",
            "members": [{"user_id": user.id, "rol_scrum": "Dev BackEnd"}],
        },
        headers=_headers(token),
    )

    assert r.status_code == 201
    dias = r.json()["design_sprint_days"]

    for dia in dias:
        assert dia["completado"] == 0
        assert dia["evidencia_url"] is None
        assert dia["plan_descripcion"] is None
        assert dia["fecha_planeada"] is None
        assert dia["comentario_docente"] is None


def test_dos_equipos_tienen_dias_independientes(client, db_session):
    """
    Crear dos equipos distintos genera 5 dias para cada uno,
    sin mezclar los registros entre equipos.
    """
    user1 = _crear_usuario(db_session, "30000005", "miembro5@cbtis75.edu.mx")
    user2 = _crear_usuario(db_session, "30000006", "miembro6@cbtis75.edu.mx")
    db_session.commit()

    token1 = _token_de(client, "miembro5@cbtis75.edu.mx")
    token2 = _token_de(client, "miembro6@cbtis75.edu.mx")

    r1 = client.post(
        "/api/v1/equipo/",
        json={
            "nombre_proyecto": "Equipo Alpha",
            "members": [{"user_id": user1.id, "rol_scrum": "Scrum Master"}],
        },
        headers=_headers(token1),
    )
    r2 = client.post(
        "/api/v1/equipo/",
        json={
            "nombre_proyecto": "Equipo Beta",
            "members": [{"user_id": user2.id, "rol_scrum": "Scrum Master"}],
        },
        headers=_headers(token2),
    )

    assert r1.status_code == 201
    assert r2.status_code == 201

    team1_id = r1.json()["id"]
    team2_id = r2.json()["id"]
    assert team1_id != team2_id

    dias_team1 = (
        db_session.query(DesignSprintDay)
        .filter(DesignSprintDay.team_id == team1_id)
        .all()
    )
    dias_team2 = (
        db_session.query(DesignSprintDay)
        .filter(DesignSprintDay.team_id == team2_id)
        .all()
    )

    assert len(dias_team1) == 5
    assert len(dias_team2) == 5

    for d in dias_team1:
        assert d.team_id == team1_id
    for d in dias_team2:
        assert d.team_id == team2_id
