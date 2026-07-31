"""
Tests del Kanban.

Cubre el issue de "notificación al Scrum Master cuando una tarea recibe
una evidencia pendiente de aprobación":

- Al subir evidencia, el Scrum Master recibe una notificación.
- Queda registrado en logs que se envió.
"""
import logging
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from app.core.security import hash_password
from app.models.sprint import Sprint
from app.models.task import Task, EstadoKanban, Prioridad
from app.models.team import Team, TeamMember
from app.models.user import RolUsuario, User


# ---------------------------------------------------------------------------
# Helpers (mismos patrones que test_backlog.py, mantenemos consistencia)
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


def _preparar_equipo_con_scrum_master_y_tarea(db):
    """
    Escenario mínimo para probar el flujo de notificación:
    - 1 estudiante (dueño de la tarea)
    - 1 scrum master (destinatario de la notificación)
    - 1 equipo con ambos como TeamMember (Scrum Master identificado por rol_scrum)
    - 1 sprint activo
    - 1 tarea sin evidencia todavía
    """
    estudiante = _crear_usuario(db, "60000001", "estu_kanban@cbtis75.edu.mx")
    scrum_master = _crear_usuario(
        db, "60000002", "sm_kanban@cbtis75.edu.mx", rol=RolUsuario.SCRUM_MASTER,
    )

    team = Team(nombre_proyecto="Equipo Kanban", grupo="Z")
    db.add(team)
    db.flush()

    db.add(TeamMember(team_id=team.id, user_id=estudiante.id, rol_scrum="Dev FrontEnd"))
    db.add(TeamMember(team_id=team.id, user_id=scrum_master.id, rol_scrum="Scrum Master"))

    sprint = Sprint(
        team_id=team.id,
        numero_parcial=1,
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=14),
    )
    db.add(sprint)
    db.flush()

    tarea = Task(
        sprint_id=sprint.id,
        asignado_a=estudiante.id,
        nombre_actividad="Implementar login",
        descripcion="Formulario y llamada al backend",
        criterios_aceptacion="Redirige a /dashboard tras login exitoso",
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=3),
        tiempo_estimado_horas=6,
        prioridad=Prioridad.ALTA,
        story_points=5,
        estado_kanban=EstadoKanban.HACIENDO,
        aprobado_por_scrum_master=False,  # importante: aún sin aprobar
    )
    db.add(tarea)
    db.commit()
    db.refresh(tarea)

    return estudiante, scrum_master, tarea


# ---------------------------------------------------------------------------
# Test principal del issue
# ---------------------------------------------------------------------------

def test_subir_evidencia_notifica_scrum_master_y_queda_en_logs(
    client, db_session, caplog, monkeypatch,
):
    """
    Criterios del issue:
    1) Al subir evidencia el Scrum Master recibe una notificación.
    2) Queda registrado en logs que se envió.

    Estrategia:
    - Mock del Notifier concreto para poder asertar QUE fue llamado y
      CON QUÉ email/mensaje (sin depender de red ni de una API real).
    - caplog para capturar el log estructurado que emite el servicio.
    """
    estudiante, scrum_master, tarea = _preparar_equipo_con_scrum_master_y_tarea(
        db_session,
    )
    token_estudiante = _token_de(client, estudiante.email)

    # --- Mock del notifier ---
    # NotificationFactory.get_notifier() se resuelve en tiempo de ejecución
    # dentro del servicio. Parcheamos la referencia importada AHÍ (no en el
    # módulo factory) — regla estándar de monkeypatching en Python.
    fake_notifier = MagicMock()
    monkeypatch.setattr(
        "app.services.evidence_notification_service.NotificationFactory.get_notifier",
        lambda: fake_notifier,
    )

    # --- Capturamos logs INFO del servicio ---
    caplog.set_level(
        logging.INFO, logger="app.services.evidence_notification_service"
    )

    # --- Actúa: subir evidencia via PATCH /mover ---
    r = client.patch(
        f"/api/v1/historia/{tarea.id}/mover",
        json={
            "nuevo_estado": "haciendo",
            "evidencia_url": "https://res.cloudinary.com/paec/evidencias/login.png",
        },
        headers=_headers(token_estudiante),
    )

    # --- Assert HTTP ---
    assert r.status_code == 200, f"Respuesta inesperada: {r.status_code} {r.text}"

    # --- Assert criterio #1: notifier fue llamado con destinatario y mensaje ---
    fake_notifier.send.assert_called_once()
    destinatario, mensaje = fake_notifier.send.call_args.args
    assert destinatario == scrum_master.email, (
        f"Se esperaba notificar a {scrum_master.email} pero llegó a {destinatario}"
    )
    assert "evidencia" in mensaje.lower()
    assert str(tarea.id) in mensaje

    # --- Assert criterio #2: quedó registro en logs ---
    log_records = [r for r in caplog.records if "Notificacion" in r.message]
    assert len(log_records) == 1, (
        f"Se esperaba exactamente 1 log de notificación, hubo {len(log_records)}."
    )
    log_msg = log_records[0].getMessage()
    assert scrum_master.email in log_msg
    assert f"id={tarea.id}" in log_msg


# ---------------------------------------------------------------------------
# Test defensivo: sin evidencia nueva NO notifica
# ---------------------------------------------------------------------------

def test_mover_tarea_sin_evidencia_no_notifica(client, db_session, monkeypatch):
    """
    Cambiar solo el estado de la tarea (sin adjuntar evidencia_url) NO debe
    disparar notificación. Evita spam al Scrum Master.
    """
    estudiante, _sm, tarea = _preparar_equipo_con_scrum_master_y_tarea(db_session)
    token = _token_de(client, estudiante.email)

    fake_notifier = MagicMock()
    monkeypatch.setattr(
        "app.services.evidence_notification_service.NotificationFactory.get_notifier",
        lambda: fake_notifier,
    )

    r = client.patch(
        f"/api/v1/historia/{tarea.id}/mover",
        json={"nuevo_estado": "haciendo", "comentario": "Sigo trabajando en esto."},
        headers=_headers(token),
    )

    assert r.status_code == 200
    fake_notifier.send.assert_not_called()


# ---------------------------------------------------------------------------
# Tests del issue: regla de evidencia obligatoria para mover a Terminado
# ---------------------------------------------------------------------------

def test_mover_a_terminado_sin_evidencia_ni_comentario_retorna_400(client, db_session):
    """
    Criterio de aceptacion principal del issue:
    Intentar mover una tarea a 'terminado' sin adjuntar evidencia_url
    ni comentario debe retornar HTTP 400 con un mensaje claro.

    Esta es la regla de negocio que protege que nadie pueda marcar
    una tarea como terminada sin aportar prueba de ello.
    """
    estudiante, _sm, tarea = _preparar_equipo_con_scrum_master_y_tarea(db_session)
    token = _token_de(client, estudiante.email)

    r = client.patch(
        f"/api/v1/historia/{tarea.id}/mover",
        json={"nuevo_estado": "terminado"},  # sin evidencia_url ni comentario
        headers=_headers(token),
    )

    assert r.status_code == 400, (
        f"Se esperaba 400 al mover a terminado sin evidencia, "
        f"pero se obtuvo {r.status_code}: {r.text}"
    )
    detalle = r.json()["detail"].lower()
    assert "evidencia" in detalle or "terminado" in detalle, (
        f"El mensaje de error no menciona evidencia ni terminado: '{detalle}'"
    )


def test_mover_a_terminado_con_evidencia_url_retorna_200(client, db_session, monkeypatch):
    """
    Con evidencia_url adjunta, mover a 'terminado' debe ser permitido (200).
    """
    estudiante, _sm, tarea = _preparar_equipo_con_scrum_master_y_tarea(db_session)
    token = _token_de(client, estudiante.email)

    monkeypatch.setattr(
        "app.services.evidence_notification_service.NotificationFactory.get_notifier",
        lambda: MagicMock(),
    )

    r = client.patch(
        f"/api/v1/historia/{tarea.id}/mover",
        json={
            "nuevo_estado": "terminado",
            "evidencia_url": "https://res.cloudinary.com/paec/evidencias/prueba.png",
        },
        headers=_headers(token),
    )

    assert r.status_code == 200
    assert r.json()["estado_kanban"] == "terminado"


def test_mover_a_terminado_solo_con_comentario_retorna_200(client, db_session, monkeypatch):
    """
    Con comentario (sin evidencia_url), mover a 'terminado' tambien
    debe ser permitido segun la regla: evidencia_url OR comentario.
    """
    estudiante, _sm, tarea = _preparar_equipo_con_scrum_master_y_tarea(db_session)
    token = _token_de(client, estudiante.email)

    monkeypatch.setattr(
        "app.services.evidence_notification_service.NotificationFactory.get_notifier",
        lambda: MagicMock(),
    )

    r = client.patch(
        f"/api/v1/historia/{tarea.id}/mover",
        json={
            "nuevo_estado": "terminado",
            "comentario": "Se completo la integracion y paso todas las pruebas.",
        },
        headers=_headers(token),
    )

    assert r.status_code == 200
    assert r.json()["estado_kanban"] == "terminado"


def test_mover_entre_estados_intermedios_sin_evidencia_es_permitido(client, db_session, monkeypatch):
    """
    La regla de evidencia obligatoria aplica UNICAMENTE a 'terminado'.
    Mover de 'por_hacer' a 'haciendo' sin evidencia debe ser 200.
    """
    estudiante, _sm, _ = _preparar_equipo_con_scrum_master_y_tarea(db_session)

    # Crear tarea en estado por_hacer
    from app.models.sprint import Sprint
    sprint = db_session.query(Sprint).filter(Sprint.team_id != None).first()
    tarea_nueva = Task(
        sprint_id=sprint.id,
        asignado_a=estudiante.id,
        nombre_actividad="Tarea por hacer",
        descripcion="Desc",
        criterios_aceptacion="Criterio",
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=5),
        tiempo_estimado_horas=2,
        story_points=1,
        estado_kanban=EstadoKanban.POR_HACER,
    )
    db_session.add(tarea_nueva)
    db_session.commit()
    db_session.refresh(tarea_nueva)

    monkeypatch.setattr(
        "app.services.evidence_notification_service.NotificationFactory.get_notifier",
        lambda: MagicMock(),
    )

    token = _token_de(client, estudiante.email)
    r = client.patch(
        f"/api/v1/historia/{tarea_nueva.id}/mover",
        json={"nuevo_estado": "haciendo"},  # sin evidencia: debe ser OK
        headers=_headers(token),
    )

    assert r.status_code == 200
    assert r.json()["estado_kanban"] == "haciendo"


def test_mover_a_terminado_tarea_inexistente_retorna_404(client, db_session):
    """
    Si el id de la tarea no existe, el endpoint retorna 404,
    independientemente de si se adjunta evidencia o no.
    """
    estudiante, _sm, _tarea = _preparar_equipo_con_scrum_master_y_tarea(db_session)
    token = _token_de(client, estudiante.email)

    r = client.patch(
        "/api/v1/historia/999999/mover",
        json={
            "nuevo_estado": "terminado",
            "evidencia_url": "https://ejemplo.com/evidencia.png",
        },
        headers=_headers(token),
    )

    assert r.status_code == 404


def test_mover_kanban_sin_autenticacion_retorna_401(client, db_session):
    """
    El endpoint PATCH /mover requiere token de autenticacion.
    Sin token debe retornar 401, sin importar el payload.
    """
    _estudiante, _sm, tarea = _preparar_equipo_con_scrum_master_y_tarea(db_session)

    r = client.patch(
        f"/api/v1/historia/{tarea.id}/mover",
        json={
            "nuevo_estado": "terminado",
            "evidencia_url": "https://ejemplo.com/evidencia.png",
        },
        # sin Authorization header
    )

    assert r.status_code == 401
