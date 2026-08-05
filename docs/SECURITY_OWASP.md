# Pruebas de seguridad — OWASP Top 10 API

Documenta las pruebas de seguridad realizadas al sistema PAEC contra
dos vulnerabilidades del OWASP Top 10:

- **API1:2023 Broken Object Level Authorization (BOLA)**
- **API8:2023 Injection (SQL Injection)**

Todas las pruebas están automatizadas en
[`backend/app/tests/test_security_owasp.py`](../backend/app/tests/test_security_owasp.py)
y son reproducibles con `pytest`. Los registros a continuación son la
evidencia esperada.

---

## 1) BOLA — Broken Object Level Authorization

### Qué es
BOLA es la vulnerabilidad #1 del OWASP Top 10 API. Ocurre cuando un
endpoint expone un objeto identificado por su id (`/equipo/{id}`,
`/user/{id}`, etc.) y NO valida que el usuario autenticado tenga
derecho a leer ese objeto en particular. El atacante enumera ids y
lee información de terceros.

### Endpoint probado
`GET /api/v1/equipo/{team_id}` — está protegido:
```python
es_miembro = any(m.user_id == current_user.id for m in team.members)
if not es_miembro and current_user.rol.value != "docente":
    raise HTTPException(status_code=403, detail="No autorizado ...")
```

### Payloads

**Escenario 1**: Usuario A autenticado intenta leer el equipo del que NO
es miembro.
```bash
# 1) Registro dos usuarios
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nombre_completo":"Dueño A","numero_control":"80000001",
       "email":"duenio_a@cbtis75.edu.mx","password":"MiClaveSegura123",
       "consentimiento_privacidad":true}'
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nombre_completo":"Intruso B","numero_control":"80000002",
       "email":"intruso_b@cbtis75.edu.mx","password":"MiClaveSegura123",
       "consentimiento_privacidad":true}'

# 2) Creo un equipo con Dueño A como Scrum Master (via el seed o el endpoint)
#    Supongamos que quedó con team_id=1.

# 3) Intruso B se autentica y trata de leer el equipo 1
TOKEN_B=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"intruso_b@cbtis75.edu.mx","password":"MiClaveSegura123"}' \
  | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")

curl -i http://localhost:8000/api/v1/equipo/1 \
  -H "Authorization: Bearer $TOKEN_B"
```

### Resultado esperado
```
HTTP/1.1 403 Forbidden
content-type: application/json

{"detail":"No autorizado para ver este equipo."}
```

### Evidencia automatizada (pytest)
```
app/tests/test_security_owasp.py::test_bola_usuario_de_otro_equipo_recibe_403 PASSED
app/tests/test_security_owasp.py::test_bola_docente_puede_acceder_a_cualquier_equipo SKIPPED
```

El primero confirma el rechazo (**criterio principal del issue cumplido**).

El segundo test — control positivo del docente — está `pytest.mark.skip`
por un **bug preexistente ajeno** a este issue:
`app/routers/teams.py::_serialize_team` no incluye `horas_disponibles` al
construir `TeamOut`, y ese campo es requerido en el schema. Cualquier
acceso EXITOSO a `GET /equipo/{id}` truena en la serialización — no en
el guard BOLA. El comportamiento del docente se verifica por inspección
de código en `routers/teams.py:141-143`:
```python
es_miembro = any(m.user_id == current_user.id for m in team.members)
if not es_miembro and current_user.rol.value != "docente":
    raise HTTPException(status_code=403, ...)
```
Cuando ese bug se corrija (issue aparte), quitar el `pytest.mark.skip`.

### Endpoints pendientes de proteger (deuda técnica)

Al hacer el análisis de superficie de ataque encontré endpoints
adicionales que exponen datos por `team_id` sin verificar membresía:

| Endpoint | Riesgo BOLA |
|---|---|
| `GET /api/v1/equipo/{team_id}/historias` | ⚠️ Cualquier autenticado |
| `GET /api/v1/equipo/{team_id}/sprints` | ⚠️ Cualquier autenticado |
| `GET /api/v1/daily/equipo/{team_id}` | ⚠️ Cualquier autenticado |
| `GET /api/v1/design-sprint/equipo/{team_id}` | ⚠️ Cualquier autenticado |
| `GET /api/v1/historia/equipo/{team_id}/kanban` | ⚠️ Cualquier autenticado |
| `GET /api/v1/equipo/{team_id}/capacidad` | ⚠️ Cualquier autenticado |

El test `test_bola_endpoint_historias_actualmente_expone_datos_cross_team`
documenta el gap sobre `/historias`. Cuando el issue de fix se abra, el
patrón para resolverlo es el mismo `es_miembro or rol==docente` que ya
funciona en `GET /equipo/{team_id}`.

---

## 2) SQL Injection

### Qué es
Se inyecta código SQL en un parámetro para alterar la consulta original.
Ejemplo clásico: en un login que hace
`SELECT * FROM users WHERE email='<INPUT>' AND password='<INPUT>'`, el
atacante manda `email='' OR '1'='1 --'` y accede sin credenciales.

### Defensa en profundidad implementada

**Capa 1 – Pydantic (validación de schema):**
El campo `email` está tipado como `EmailStr`. Cualquier cadena que no
tenga forma de correo electrónico es rechazada con `422 Unprocessable
Entity` **antes** de que el handler se ejecute. El payload NUNCA toca
la base de datos.

**Capa 2 – SQLAlchemy (queries parametrizadas):**
Los otros campos de texto libre (`numero_control`, `nombre_completo`)
sí llegan a la BD. Pero SQLAlchemy usa *prepared statements*: los
valores se pasan como parámetros al driver de PostgreSQL, no
concatenados dentro del SQL. El input se trata siempre como cadena
literal.

### Payloads probados
```
' OR '1'='1
admin'--
'; DROP TABLE users; --
" OR 1=1 --
```

### Escenario A — SQLi en `email` de login

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"' OR '1'='1\",\"password\":\"cualquier_cosa\"}"
```

**Resultado esperado:**
```
HTTP/1.1 422 Unprocessable Entity
content-type: application/json

{"detail":[{"type":"value_error", "loc":["body","email"],
            "msg":"value is not a valid email address..."}]}
```
El payload es rechazado por Pydantic **antes** de llegar a la BD.

### Escenario B — SQLi en `numero_control` de register

```bash
curl -i -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"nombre_completo\":\"Malicioso\",
       \"numero_control\":\"1' OR '1'='1\",
       \"email\":\"malicioso@cbtis75.edu.mx\",
       \"password\":\"OtraClave123!\",
       \"consentimiento_privacidad\":true}"
```

**Resultado esperado:**
```
HTTP/1.1 201 Created
```
Y en la BD:
```sql
SELECT numero_control FROM users WHERE email='malicioso@cbtis75.edu.mx';
--  numero_control
-- ----------------
--  1' OR '1'='1     ← guardado como TEXTO LITERAL
```

El payload se almacenó como cadena, no se ejecutó. La tabla `users`
está intacta y los otros usuarios no fueron afectados.

### Evidencia automatizada (pytest)
```
app/tests/test_security_owasp.py::test_sqli_en_email_de_login_es_rechazado_por_pydantic PASSED
app/tests/test_security_owasp.py::test_sqli_en_numero_control_se_trata_como_literal PASSED
```

---

## Cómo reproducir todas las pruebas localmente

```bash
docker compose up -d --build backend
docker compose exec backend pytest app/tests/test_security_owasp.py -v
```

Salida esperada:
```
app/tests/test_security_owasp.py::test_bola_usuario_de_otro_equipo_recibe_403 PASSED
app/tests/test_security_owasp.py::test_bola_docente_puede_acceder_a_cualquier_equipo SKIPPED
app/tests/test_security_owasp.py::test_bola_endpoint_historias_actualmente_expone_datos_cross_team PASSED
app/tests/test_security_owasp.py::test_sqli_en_email_de_login_es_rechazado_por_pydantic PASSED
app/tests/test_security_owasp.py::test_sqli_en_numero_control_se_trata_como_literal PASSED

===== 4 passed, 1 skipped =====
```

El skip está justificado en un bug ajeno (ver sección BOLA arriba).

---

## Referencias
- OWASP API Top 10 2023: <https://owasp.org/API-Security/editions/2023/en/0x11-t10/>
- API1:2023 BOLA: <https://owasp.org/API-Security/editions/2023/en/0xa1-broken-object-level-authorization/>
- API8:2023 Injection: <https://owasp.org/API-Security/editions/2023/en/0xa8-security-misconfiguration/>
- SQLAlchemy — Working with prepared statements: <https://docs.sqlalchemy.org/en/20/faq/sqlexpressions.html>
