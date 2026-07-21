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
    """Criterio 1: segundo registro con mismo email -> 400 con mensaje genérico."""
    payload = _payload_valido(
        email="duplicado@cbtis75.edu.mx",
        numero_control="21380003",
    )
    r1 = client.post("/api/v1/auth/register", json=payload)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/auth/register", json=payload)
    assert r2.status_code == 400


def test_register_numero_control_duplicado_devuelve_400(client):
    """La validación cubre AMBOS campos: mismo numero_control con email distinto también -> 400."""
    r1 = client.post(
        "/api/v1/auth/register",
        json=_payload_valido(
            email="primero@cbtis75.edu.mx",
            numero_control="21380004",
        ),
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/v1/auth/register",
        json=_payload_valido(
            email="otro@cbtis75.edu.mx",  # email distinto
            numero_control="21380004",    # mismo numero_control
        ),
    )
    assert r2.status_code == 400


def test_register_duplicado_no_revela_que_campo_conflictuo(client):
    """Criterio 2: el mensaje NO debe mencionar 'email' ni 'numero_control'
    para no filtrar información sobre qué cuentas existen (enumeración de usuarios).
    """
    payload = _payload_valido(
        email="secreto@cbtis75.edu.mx",
        numero_control="21380005",
    )
    client.post("/api/v1/auth/register", json=payload)
    r = client.post("/api/v1/auth/register", json=payload)

    assert r.status_code == 400
    mensaje = r.json()["detail"].lower()
    assert "email" not in mensaje
    assert "numero_control" not in mensaje
    assert "correo" not in mensaje
    assert "control" not in mensaje


# --- Tests Issue #6: restricción de rol en registro público -----------------

def test_registro_publico_con_rol_docente_queda_como_estudiante(client, db_session):
    """
    Criterio de aceptación #6-1:
    Enviar rol=docente al endpoint público /register debe resultar en un
    usuario con rol=estudiante. El campo 'rol' no existe en UserCreatePublic,
    por lo que Pydantic lo ignora y el handler fuerza ESTUDIANTE.
    """
    payload = {
        "nombre_completo": "Atacante Rol",
        "numero_control": "21390001",
        "email": "atacante_docente@cbtis75.edu.mx",
        "password": "ClaveSegura789",
        "rol": "docente",  # intento de escalada de privilegios
    }
    r = client.post("/api/v1/auth/register", json=payload)

    assert r.status_code == 201
    body = r.json()
    # El rol devuelto debe ser estudiante, no docente
    assert body["rol"] == "estudiante", (
        f"Se esperaba 'estudiante' pero se obtuvo '{body['rol']}'. "
        "El endpoint público no debe aceptar rol=docente."
    )

    # Verificar directamente en BD que tampoco se guardó como docente
    user = db_session.query(User).filter(User.email == payload["email"]).first()
    assert user is not None
    assert user.rol.value == "estudiante"


def test_registro_publico_con_rol_scrum_master_queda_como_estudiante(client, db_session):
    """
    Criterio de aceptación #6-1 (variante):
    Enviar rol=scrum_master al endpoint público también debe resultar en estudiante.
    """
    payload = {
        "nombre_completo": "Atacante Scrum",
        "numero_control": "21390002",
        "email": "atacante_scrum@cbtis75.edu.mx",
        "password": "ClaveSegura789",
        "rol": "scrum_master",  # otro intento de escalada
    }
    r = client.post("/api/v1/auth/register", json=payload)

    assert r.status_code == 201
    assert r.json()["rol"] == "estudiante"

    user = db_session.query(User).filter(User.email == payload["email"]).first()
    assert user.rol.value == "estudiante"


def test_registro_publico_omitir_rol_queda_como_estudiante(client):
    """
    Caso base: si no se envía el campo rol, el resultado sigue siendo estudiante.
    """
    payload = {
        "nombre_completo": "Usuario Sin Rol",
        "numero_control": "21390003",
        "email": "sinrol@cbtis75.edu.mx",
        "password": "ClaveSegura789",
        # sin campo 'rol'
    }
    r = client.post("/api/v1/auth/register", json=payload)

    assert r.status_code == 201
    assert r.json()["rol"] == "estudiante"


def test_register_docente_sin_token_retorna_401(client):
    """
    Criterio de aceptación #6-2:
    El endpoint protegido /register/docente debe rechazar peticiones
    sin token de autenticación con 401.
    """
    payload = {
        "nombre_completo": "Nuevo Docente",
        "numero_control": "21390004",
        "email": "nuevo_docente@cbtis75.edu.mx",
        "password": "ClaveDocente123",
        "rol": "docente",
    }
    r = client.post("/api/v1/auth/register/docente", json=payload)

    assert r.status_code == 401


def test_register_docente_con_token_de_estudiante_retorna_403(client):
    """
    Criterio de aceptación #6-2:
    Un estudiante autenticado NO puede usar /register/docente. Debe recibir 403.
    """
    # 1. Crear y autenticar un estudiante
    client.post(
        "/api/v1/auth/register",
        json={
            "nombre_completo": "Estudiante Normal",
            "numero_control": "21390005",
            "email": "estudiante_normal@cbtis75.edu.mx",
            "password": "ClaveEstudiante123",
        },
    )
    login_r = client.post(
        "/api/v1/auth/login",
        json={
            "email": "estudiante_normal@cbtis75.edu.mx",
            "password": "ClaveEstudiante123",
        },
    )
    assert login_r.status_code == 200
    token = login_r.json()["access_token"]

    # 2. Intentar crear un docente usando el token del estudiante
    r = client.post(
        "/api/v1/auth/register/docente",
        json={
            "nombre_completo": "Docente Falso",
            "numero_control": "21390006",
            "email": "docente_falso@cbtis75.edu.mx",
            "password": "ClaveDocente456",
            "rol": "docente",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 403
