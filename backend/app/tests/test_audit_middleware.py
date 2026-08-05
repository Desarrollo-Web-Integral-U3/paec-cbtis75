"""
Tests del Middleware de Auditoria.

Criterios de aceptacion:
1. Cada request queda registrado con metodo, ruta, user_id y fecha/hora.
2. El log NUNCA contiene el cuerpo del request ni contrasenas.

Estrategia:
- Se usa `caplog` de pytest para capturar los registros emitidos por el
  logger "app.audit" sin necesidad de archivos ni mocks de logging.
- Se verifica presencia y ausencia de informacion en los mensajes.
"""
import logging
from datetime import datetime

import pytest

from app.core.security import hash_password
from app.models.user import User, RolUsuario


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _crear_usuario(db, numero_control, email, rol=RolUsuario.ESTUDIANTE):
    user = User(
        nombre_completo="Audit Test User",
        numero_control=numero_control,
        email=email,
        password_hash=hash_password("Password123"),
        rol=rol,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _token_de(client, email, password="Password123"):
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, f"Login fallo: {r.json()}"
    return r.json()["access_token"]


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


def _obtener_logs_auditoria(caplog):
    """Devuelve los registros del logger 'app.audit' capturados."""
    return [r for r in caplog.records if r.name == "app.audit"]


# ---------------------------------------------------------------------------
# Criterio 1: Cada request queda registrado con metodo, ruta, user_id y timestamp
# ---------------------------------------------------------------------------

def test_audit_log_registra_metodo_y_ruta(client, db_session, caplog):
    """
    Una peticion GET al health-check debe generar un log de auditoria
    que incluya el metodo HTTP y la ruta exacta.
    """
    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.get("/api/v1/health")

    logs = _obtener_logs_auditoria(caplog)
    assert len(logs) >= 1, "No se genero ningun log de auditoria"

    ultimo = logs[-1].getMessage()
    assert "GET" in ultimo, f"El log no contiene el metodo GET: {ultimo}"
    assert "/api/v1/health" in ultimo, f"El log no contiene la ruta: {ultimo}"


def test_audit_log_registra_user_id_autenticado(client, db_session, caplog):
    """
    Cuando el request lleva un JWT valido, el log debe incluir el user_id
    real del usuario autenticado (no 'anonimo').
    """
    user = _crear_usuario(db_session, "70000001", "audit1@cbtis75.edu.mx")
    token = _token_de(client, "audit1@cbtis75.edu.mx")

    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.get("/api/v1/health", headers=_headers(token))

    logs = _obtener_logs_auditoria(caplog)
    assert len(logs) >= 1

    ultimo = logs[-1].getMessage()
    assert f"user_id={user.id}" in ultimo, (
        f"El log debe contener user_id={user.id}, pero dice: {ultimo}"
    )
    assert "anonimo" not in ultimo, (
        "El log no debe decir 'anonimo' cuando el usuario esta autenticado"
    )


def test_audit_log_registra_anonimo_sin_token(client, db_session, caplog):
    """
    Cuando el request NO lleva token, el log debe registrar 'anonimo'
    como user_id (no debe fallar ni revelar nada sensible).
    """
    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.get("/api/v1/health")  # sin Authorization header

    logs = _obtener_logs_auditoria(caplog)
    assert len(logs) >= 1

    ultimo = logs[-1].getMessage()
    assert "user_id=anonimo" in ultimo, (
        f"El log debe indicar 'anonimo' para requests sin token: {ultimo}"
    )


def test_audit_log_incluye_timestamp_formato_iso(client, db_session, caplog):
    """
    El log de auditoria debe incluir la fecha/hora en formato ISO-8601.
    Se comprueba que el campo 'timestamp=' aparece y que contiene
    al menos el ano actual (verificacion minima sin acoplar al segundo exacto).
    """
    ano_actual = str(datetime.utcnow().year)

    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.get("/api/v1/health")

    logs = _obtener_logs_auditoria(caplog)
    assert len(logs) >= 1

    ultimo = logs[-1].getMessage()
    assert "timestamp=" in ultimo, f"El log no contiene campo timestamp: {ultimo}"
    assert ano_actual in ultimo, (
        f"El timestamp no contiene el ano {ano_actual}: {ultimo}"
    )


def test_audit_log_registra_distintos_metodos_http(client, db_session, caplog):
    """
    El middleware debe funcionar para cualquier metodo HTTP.
    Se prueba con un POST (login) y se verifica que el metodo aparezca en el log.
    """
    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.post(
            "/api/v1/auth/login",
            json={"email": "noexiste@test.com", "password": "cualquiera"},
        )

    logs = _obtener_logs_auditoria(caplog)
    assert len(logs) >= 1

    ultimo = logs[-1].getMessage()
    assert "POST" in ultimo, f"El log del POST no contiene el metodo: {ultimo}"
    assert "/api/v1/auth/login" in ultimo


# ---------------------------------------------------------------------------
# Criterio 2: El log NUNCA contiene el body ni contrasenas
# ---------------------------------------------------------------------------

def test_audit_log_nunca_contiene_body_del_request(client, db_session, caplog):
    """
    GARANTIA DE PRIVACIDAD principal: el log de auditoria NO debe incluir
    el cuerpo de la peticion. Se envia un JSON con datos sensibles y se
    verifica que ninguno aparezca en los logs.
    """
    email_secreto = "secreto_no_debe_aparecer@test.com"
    contrasena_secreta = "MiContrasenaMuySecreta123!"

    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.post(
            "/api/v1/auth/login",
            json={"email": email_secreto, "password": contrasena_secreta},
        )

    for record in _obtener_logs_auditoria(caplog):
        mensaje = record.getMessage()
        assert contrasena_secreta not in mensaje, (
            f"FALLO DE SEGURIDAD: la contrasena aparece en el log de auditoria: {mensaje}"
        )
        assert email_secreto not in mensaje, (
            f"El email del body no debe aparecer en el log de auditoria: {mensaje}"
        )


def test_audit_log_nunca_contiene_token_completo(client, db_session, caplog):
    """
    El JWT completo (token) NO debe aparecer en el log.
    Solo el user_id extraido del payload puede aparecer.
    """
    user = _crear_usuario(db_session, "70000002", "audit2@cbtis75.edu.mx")
    token = _token_de(client, "audit2@cbtis75.edu.mx")

    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.get("/api/v1/health", headers=_headers(token))

    for record in _obtener_logs_auditoria(caplog):
        mensaje = record.getMessage()
        assert token not in mensaje, (
            f"FALLO DE SEGURIDAD: el token JWT completo aparece en el log: {mensaje[:80]}..."
        )


def test_audit_log_no_expone_datos_sensibles_en_body_de_registro(client, db_session, caplog):
    """
    Al registrar un nuevo usuario (POST /register), el body contiene
    datos personales. El log de auditoria solo debe registrar metadatos.
    """
    numero_secreto = "99887766"
    contrasena_secreta = "ClavePrivada456!"

    with caplog.at_level(logging.INFO, logger="app.audit"):
        client.post(
            "/api/v1/auth/register",
            json={
                "nombre_completo": "Usuario Prueba Audit",
                "numero_control": numero_secreto,
                "email": "audit_reg@cbtis75.edu.mx",
                "password": contrasena_secreta,
            },
        )

    for record in _obtener_logs_auditoria(caplog):
        mensaje = record.getMessage()
        assert contrasena_secreta not in mensaje, (
            f"FALLO: la contrasena del registro aparece en el audit log: {mensaje}"
        )
        assert numero_secreto not in mensaje, (
            f"El numero de control no debe aparecer en el audit log: {mensaje}"
        )
