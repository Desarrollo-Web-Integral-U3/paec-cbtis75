"""
Tests del rate limiting en el endpoint POST /api/v1/auth/login.

Criterio de aceptacion:
- Al sexto intento de login en menos de un minuto se recibe HTTP 429.
- Los primeros 5 intentos deben procesarse normalmente (200 o 401, nunca 429).

Notas de implementacion:
- slowapi usa como key la IP del cliente. En el TestClient de Starlette,
  request.client.host siempre es "testclient", por lo que todos los requests
  de un mismo test comparten el mismo contador de rate limit.
- Para aislar tests entre si se usa un fixture `reset_limiter` que llama a
  limiter._storage.reset() antes de cada test, limpiando todos los contadores.
- Esto simula fielmente el comportamiento real: cada "cliente nuevo" llega
  con su contador en cero.
"""
import pytest
from app.core.rate_limit import limiter

LOGIN_URL = "/api/v1/auth/login"
PAYLOAD_INVALIDO = {"email": "noexiste@test.com", "password": "mal"}


# ---------------------------------------------------------------------------
# Fixture: resetea el storage del limiter antes de cada test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_limiter():
    """
    Limpia todos los contadores del rate limiter antes de cada test.
    Sin esto, los intentos de un test se acumulan en el siguiente,
    causando falsos 429.
    """
    limiter._storage.reset()
    yield
    limiter._storage.reset()  # limpieza tambien al salir


# ---------------------------------------------------------------------------
# Criterio principal: 6to intento -> 429
# ---------------------------------------------------------------------------

def test_sexto_intento_login_retorna_429(client):
    """
    CRITERIO DEL ISSUE: el sexto intento de login desde el mismo origen
    en menos de un minuto debe retornar HTTP 429 Too Many Requests.

    Los primeros 5 intentos pueden retornar 200 o 401 (credenciales invalidas),
    pero NUNCA 429.
    """
    # Intentos 1 a 5: deben pasar el rate limiter (retornan 401 por creds invalidas)
    for intento in range(1, 6):
        r = client.post(LOGIN_URL, json=PAYLOAD_INVALIDO)
        assert r.status_code != 429, (
            f"Intento {intento}/5: no deberia recibir 429 aun, "
            f"pero se obtuvo {r.status_code}"
        )

    # Intento 6: debe ser bloqueado por el rate limiter -> 429
    r = client.post(LOGIN_URL, json=PAYLOAD_INVALIDO)
    assert r.status_code == 429, (
        f"El sexto intento debe retornar 429, pero se obtuvo {r.status_code}: {r.text}"
    )


def test_primeros_cinco_intentos_retornan_401_no_429(client):
    """
    Verificacion complementaria: los primeros 5 intentos con credenciales
    invalidas NO deben recibir 429, sino 401 (credenciales invalidas).
    """
    for intento in range(1, 6):
        r = client.post(LOGIN_URL, json=PAYLOAD_INVALIDO)
        assert r.status_code == 401, (
            f"Intento {intento}: credenciales invalidas deben retornar 401, "
            f"se obtuvo {r.status_code}"
        )


def test_exactamente_cinco_intentos_no_bloquean(client):
    """
    Exactamente 5 intentos (el maximo permitido) no deben ser bloqueados.
    El limite se activa en el 6to intento, no antes.
    """
    for intento in range(1, 6):
        r = client.post(LOGIN_URL, json=PAYLOAD_INVALIDO)
        assert r.status_code != 429, (
            f"El intento {intento} no debe ser bloqueado (limite es 5/min): {r.status_code}"
        )

    # Confirmamos que el 5to fue 401 y no 429
    assert r.status_code == 401


def test_respuesta_429_tiene_mensaje_de_error(client):
    """
    La respuesta 429 debe incluir un cuerpo JSON con informacion
    sobre el error de rate limit.
    """
    # Agotar los 5 intentos
    for _ in range(5):
        client.post(LOGIN_URL, json=PAYLOAD_INVALIDO)

    # 6to intento -> 429
    r = client.post(LOGIN_URL, json=PAYLOAD_INVALIDO)

    assert r.status_code == 429
    # El body debe ser JSON valido con algun campo de error
    body = r.json()
    assert body is not None, "La respuesta 429 debe tener body JSON"
    # slowapi puede usar "error", "detail" u otro campo
    assert len(body) > 0, "El body de la respuesta 429 no debe estar vacio"


def test_otros_endpoints_no_afectados_por_limite_login(client):
    """
    El rate limit de 5/min aplica SOLO a /login.
    El endpoint /health no debe verse afectado aunque /login este bloqueado.
    """
    # Agotar y superar el rate limit de /login
    for _ in range(6):
        client.post(LOGIN_URL, json=PAYLOAD_INVALIDO)

    # /health debe seguir respondiendo 200 sin importar el rate limit de /login
    r = client.get("/api/v1/health")
    assert r.status_code == 200, (
        f"/health no debe estar bloqueado por el rate limit de /login: {r.status_code}"
    )


def test_limite_aplicado_incluso_con_credenciales_correctas(client, db_session):
    """
    El rate limit cuenta TODOS los intentos al endpoint /login,
    independientemente de si las credenciales son correctas o no.
    Despues de 5 requests al endpoint (exitosos o no), el 6to es 429.
    """
    from app.core.security import hash_password
    from app.models.user import User, RolUsuario

    # Crear un usuario real para poder hacer login exitoso
    user = User(
        nombre_completo="Rate Limit User",
        numero_control="RL000001",
        email="rate_limit@cbtis75.edu.mx",
        password_hash=hash_password("Password123"),
        rol=RolUsuario.ESTUDIANTE,
    )
    db_session.add(user)
    db_session.commit()

    payload_valido = {"email": "rate_limit@cbtis75.edu.mx", "password": "Password123"}

    # 5 logins exitosos (200) - deben pasar
    for intento in range(1, 6):
        r = client.post(LOGIN_URL, json=payload_valido)
        assert r.status_code == 200, (
            f"Login exitoso {intento} fallo: {r.status_code}"
        )

    # El 6to intento -> 429, aunque las credenciales sean correctas
    r = client.post(LOGIN_URL, json=payload_valido)
    assert r.status_code == 429, (
        f"El 6to intento debe ser 429 incluso con creds correctas: {r.status_code}"
    )
