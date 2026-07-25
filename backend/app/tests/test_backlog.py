from datetime import datetime, timedelta

from app.core.security import hash_password
from app.models.team import Team, TeamMember
from app.models.user import User, RolUsuario


def _registrar_usuario(client, email: str, numero_control: str, nombre: str = "Usuario Test"):
    r = client.post(
        "/api/v1/auth/register",
        json={
            "nombre_completo": nombre,
            "numero_control": numero_control,
            "email": email,
            "password": "ClaveSegura123",
            "rol": "estudiante",
            "consentimiento_privacidad": True,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def _login(client, email: str) -> str:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "ClaveSegura123"},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def _headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_backlog_permite_crear_historia_y_listarla_por_sprint(client, db_session):
    emails = ["sm@cbtis75.edu.mx", "dev@cbtis75.edu.mx"]
    for i, email in enumerate(emails):
        _registrar_usuario(client, email=email, numero_control=f"2138000{i}", nombre=f"Usuario {i}")

    token = _login(client, emails[0])

    team_payload = {
        "nombre_proyecto": "Proyecto Demo",
        "descripcion_proyecto": "Proyecto de prueba",
        "grupo": "6IDS-A",
        "members": [
            {"email": emails[0], "rol_scrum": "Scrum Master"},
            {"email": emails[1], "rol_scrum": "Developer"},
        ],
    }
    r = client.post("/api/v1/equipo/", json=team_payload, headers=_headers(token))
    assert r.status_code == 201, r.text
    team_id = r.json()["id"]

    ahora = datetime.utcnow()
    sprint_payload = {
        "team_id": team_id,
        "numero_parcial": 1,
        "fecha_inicio": (ahora - timedelta(days=1)).isoformat(),
        "fecha_fin": (ahora + timedelta(days=7)).isoformat(),
    }
    r = client.post("/api/v1/sprint", json=sprint_payload, headers=_headers(token))
    assert r.status_code == 201, r.text
    sprint_id = r.json()["id"]

    task_payload = {
        "sprint_id": sprint_id,
        "asignado_a": 2,
        "nombre_actividad": "Registrar usuario",
        "descripcion": "Permitir acceder con credenciales validas",
        "criterios_aceptacion": "El usuario puede registrarse y ver el login",
        "fecha_inicio": (ahora - timedelta(days=1)).isoformat(),
        "fecha_fin": (ahora + timedelta(days=3)).isoformat(),
        "tiempo_estimado_horas": 8,
        "prioridad": "alta",
        "story_points": 5,
    }
    r = client.post("/api/v1/historia", json=task_payload, headers=_headers(token))
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["nombre_actividad"] == "Registrar usuario"
    assert body["sprint_id"] == sprint_id

    r = client.get(f"/api/v1/sprint/{sprint_id}/historias", headers=_headers(token))
    assert r.status_code == 200, r.text
    historias = r.json()
    assert len(historias) == 1
    assert historias[0]["nombre_actividad"] == "Registrar usuario"
