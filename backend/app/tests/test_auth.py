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
        # Requerido desde el issue del aviso de privacidad: sin este flag
        # en True el endpoint responde 400.
        "consentimiento_privacidad": True,
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
        "consentimiento_privacidad": True,
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
        "consentimiento_privacidad": True,
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
        "consentimiento_privacidad": True,
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
        "consentimiento_privacidad": True,
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
            "consentimiento_privacidad": True,
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
            "consentimiento_privacidad": True,
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    assert r.status_code == 403


# --- Tests del issue de consentimiento del aviso de privacidad ---------------

def test_register_sin_consentimiento_devuelve_400(client):
    """
    Criterio: el endpoint debe rechazar con 400 si el usuario NO marcó el
    checkbox del aviso de privacidad (consentimiento_privacidad=false).
    """
    r = client.post(
        "/api/v1/auth/register",
        json=_payload_valido(consentimiento_privacidad=False),
    )
    assert r.status_code == 400
    assert "privacidad" in r.json()["detail"].lower()


def test_register_guarda_consentimiento_y_fecha_en_bd(client, db_session):
    """
    Criterio: la tabla users guarda consentimiento_privacidad (True) y la
    fecha_consentimiento (server-side, no la que mande el cliente).
    """
    r = client.post(
        "/api/v1/auth/register",
        json=_payload_valido(
            email="consent@cbtis75.edu.mx",
            numero_control="21380009",
        ),
    )
    assert r.status_code == 201

    user = db_session.query(User).filter(User.email == "consent@cbtis75.edu.mx").first()
    assert user is not None
    assert user.consentimiento_privacidad is True
    assert user.fecha_consentimiento is not None
    # Y también viene en la respuesta (transparencia para el cliente)
    body = r.json()
    assert body["consentimiento_privacidad"] is True
    assert body["fecha_consentimiento"] is not None


def test_token_endpoint_acepta_form_encoded(client):
    """
    El endpoint /token (usado por Swagger Authorize) acepta credenciales
    form-encoded con username=email y regresa un access_token valido.
    """
    # Registro previo por el endpoint publico normal
    client.post(
        "/api/v1/auth/register",
        json={
            "nombre_completo": "Usuario Swagger",
            "numero_control": "SW0001",
            "email": "swagger@cbtis75.edu.mx",
            "password": "Demo1234!",
            "consentimiento_privacidad": True,
        },
    )

    # Login por el nuevo endpoint form-encoded
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "swagger@cbtis75.edu.mx",
            "password": "Demo1234!",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_token_endpoint_rechaza_credenciales_invalidas(client):
    """Con password mala el endpoint /token responde 401 sin filtrar detalle."""
    response = client.post(
        "/api/v1/auth/token",
        data={
            "username": "inexistente@cbtis75.edu.mx",
            "password": "Wrong123!",
        },
    )
    assert response.status_code == 401


# --- Tests del issue: DELETE /api/v1/auth/me (ARCO / LFPDPPP) ---------------

def _registrar_y_loguear(client, email="arco@cbtis75.edu.mx", numero_control="99000001"):
    """Registra un estudiante y devuelve (id, token)."""
    r_reg = client.post(
        "/api/v1/auth/register",
        json={
            "nombre_completo": "Usuario ARCO",
            "numero_control": numero_control,
            "email": email,
            "password": "MiClaveSegura123",
            "consentimiento_privacidad": True,
        },
    )
    assert r_reg.status_code == 201, r_reg.text
    user_id = r_reg.json()["id"]

    r_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "MiClaveSegura123"},
    )
    assert r_login.status_code == 200
    token = r_login.json()["access_token"]
    return user_id, token


def test_delete_me_anonimiza_datos_personales(client, db_session):
    """
    Criterio 1: el usuario deja de mostrar datos personales identificables.
    Tras DELETE, la fila sigue existiendo pero PII fue reescrito y hay
    fecha_anonimizacion estampada.
    """
    user_id, token = _registrar_y_loguear(client)

    r = client.delete(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204
    assert r.content == b""  # 204 no lleva body

    # La fila NO fue eliminada; los campos PII fueron reescritos.
    user = db_session.query(User).filter(User.id == user_id).first()
    assert user is not None, "La fila del usuario NO debe borrarse"
    assert user.nombre_completo == "Usuario eliminado"
    assert user.email == f"eliminado+{user_id}@paec.local"
    assert user.numero_control == f"ELIM-{user_id}"
    assert user.fecha_anonimizacion is not None
    # El password hash cambió (ya no es el original), y NO está en texto plano.
    assert user.password_hash != "MiClaveSegura123"
    assert user.password_hash.startswith("$2b$")


def test_delete_me_preserva_tasks_y_dailies(client, db_session):
    """
    Criterio 2: las tareas y dailies siguen existiendo sin errores.
    Ninguna FK se rompe; siguen apuntando al mismo user_id (ahora anónimo).
    """
    from app.models.team import Team, TeamMember
    from app.models.sprint import Sprint
    from app.models.task import Task, EstadoKanban, Prioridad
    from app.models.daily import Daily
    from datetime import datetime, timedelta

    user_id, token = _registrar_y_loguear(
        client, email="arco2@cbtis75.edu.mx", numero_control="99000002",
    )

    # Sembrar un equipo + sprint + task + daily asociados a este user
    team = Team(nombre_proyecto="Equipo ARCO", grupo="Y")
    db_session.add(team)
    db_session.flush()
    db_session.add(TeamMember(team_id=team.id, user_id=user_id, rol_scrum="Developer"))
    sprint = Sprint(
        team_id=team.id,
        numero_parcial=1,
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=14),
    )
    db_session.add(sprint)
    db_session.flush()
    task = Task(
        sprint_id=sprint.id,
        asignado_a=user_id,
        nombre_actividad="Tarea histórica",
        descripcion="…",
        criterios_aceptacion="…",
        fecha_inicio=datetime.utcnow(),
        fecha_fin=datetime.utcnow() + timedelta(days=3),
        tiempo_estimado_horas=4,
        prioridad=Prioridad.MEDIA,
        story_points=3,
        estado_kanban=EstadoKanban.HACIENDO,
    )
    daily = Daily(
        team_id=team.id,
        user_id=user_id,
        que_hice_ayer="…",
        que_hare_hoy="…",
    )
    db_session.add_all([task, daily])
    db_session.commit()
    task_id, daily_id = task.id, daily.id

    # Ejercer ARCO
    r = client.delete(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 204

    # Tanto task como daily siguen existiendo y siguen apuntando al mismo user_id.
    task_after = db_session.query(Task).filter(Task.id == task_id).first()
    daily_after = db_session.query(Daily).filter(Daily.id == daily_id).first()
    assert task_after is not None, "La tarea histórica NO debe eliminarse"
    assert daily_after is not None, "El daily histórico NO debe eliminarse"
    assert task_after.asignado_a == user_id
    assert daily_after.user_id == user_id


def test_delete_me_sin_token_retorna_401(client):
    """Sin JWT no se puede ejercer el DELETE."""
    r = client.delete("/api/v1/auth/me")
    assert r.status_code == 401


def test_token_de_usuario_anonimizado_es_rechazado(client):
    """
    El JWT que tenía el usuario ANTES del DELETE deja de funcionar,
    porque get_current_user detecta fecha_anonimizacion y responde 401.
    Esto invalida sesiones viejas sin blacklist externa.
    """
    user_id, token = _registrar_y_loguear(
        client, email="arco3@cbtis75.edu.mx", numero_control="99000003",
    )
    headers = {"Authorization": f"Bearer {token}"}

    # Antes del DELETE, GET /me funciona
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200

    # Ejerce ARCO
    assert client.delete("/api/v1/auth/me", headers=headers).status_code == 204

    # Después del DELETE, el mismo JWT queda inservible
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401


def test_get_me_devuelve_datos_del_usuario_autenticado(client):
    """GET /me devuelve los datos del propio usuario (sin password)."""
    _uid, token = _registrar_y_loguear(
        client, email="perfil@cbtis75.edu.mx", numero_control="99000004",
    )
    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "perfil@cbtis75.edu.mx"
    assert "password" not in body
    assert "password_hash" not in body
