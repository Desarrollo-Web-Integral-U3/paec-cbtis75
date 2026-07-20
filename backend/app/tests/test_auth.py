"""
Tests de autenticación.

Cubre los 4 criterios de aceptación del issue "POST /api/v1/auth/register":
- Devuelve 201 con el usuario creado
- Rechaza campos faltantes con 422
- Password se guarda hasheado (bcrypt)
- Nunca en texto plano
"""
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.user import User


# --- Pruebas unitarias puras (no requieren BD) --------------------------------

def test_password_hash_roundtrip():
    plano = "MiClaveSegura123"
    hashed = hash_password(plano)
    assert hashed != plano
    assert verify_password(plano, hashed) is True
    assert verify_password("otra_clave", hashed) is False


def test_jwt_roundtrip():
    token = create_access_token({"sub": "1", "rol": "estudiante"})
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["rol"] == "estudiante"


def test_jwt_invalido():
    assert decode_access_token("token.invalido.xyz") is None


# --- Tests de endpoint POST /api/v1/auth/register -----------------------------

def _payload_valido(**overrides):
    """Payload base para registrar un usuario válido. Cada test puede sobrescribir campos."""
    base = {
        "nombre_completo": "Juan Pérez",
        "numero_control": "21380001",
        "email": "juan@cbtis75.edu.mx",
        "password": "MiClaveSegura123",
        "rol": "estudiante",
    }
    base.update(overrides)
    return base


def test_register_devuelve_201_y_excluye_password(client):
    """Criterio 1: 201 + body con datos del usuario, SIN password ni password_hash."""
    r = client.post("/api/v1/auth/register", json=_payload_valido())

    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "juan@cbtis75.edu.mx"
    assert body["nombre_completo"] == "Juan Pérez"
    assert body["numero_control"] == "21380001"
    assert body["rol"] == "estudiante"
    assert "id" in body
    # Criterio 4: la contraseña NUNCA se devuelve al cliente.
    assert "password" not in body
    assert "password_hash" not in body


def test_register_campos_faltantes_devuelve_422(client):
    """Criterio 2: falta email y password -> 422 con detalle de qué falta."""
    r = client.post(
        "/api/v1/auth/register",
        json={"nombre_completo": "Sin datos", "numero_control": "99999999"},
    )

    assert r.status_code == 422
    detail = r.json()["detail"]
    campos_faltantes = {err["loc"][-1] for err in detail}
    assert "email" in campos_faltantes
    assert "password" in campos_faltantes


def test_register_email_invalido_devuelve_422(client):
    """Validación de formato: EmailStr de Pydantic rechaza cadenas que no son email."""
    r = client.post(
        "/api/v1/auth/register",
        json=_payload_valido(email="esto-no-es-un-email"),
    )
    assert r.status_code == 422


def test_register_password_se_guarda_hasheada_con_bcrypt(client, db_session):
    """Criterios 3 y 4: la BD guarda un hash bcrypt, NUNCA la contraseña en texto plano."""
    plano = "OtraClaveSegura456"
    r = client.post(
        "/api/v1/auth/register",
        json=_payload_valido(
            email="maria@cbtis75.edu.mx",
            numero_control="21380002",
            nombre_completo="María López",
            password=plano,
        ),
    )
    assert r.status_code == 201

    user = db_session.query(User).filter(User.email == "maria@cbtis75.edu.mx").first()
    assert user is not None
    # Nunca en texto plano
    assert user.password_hash != plano
    # Formato bcrypt: $2b$<rounds>$<salt+hash>  (12 rounds por defecto de passlib)
    assert user.password_hash.startswith("$2b$")
    # El hash sí verifica la contraseña original (roundtrip)
    assert verify_password(plano, user.password_hash) is True


def test_register_email_duplicado_devuelve_400(client):
    """Regla de negocio adicional: no se puede registrar dos veces el mismo email."""
    payload = _payload_valido(
        email="duplicado@cbtis75.edu.mx",
        numero_control="21380003",
    )
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400
