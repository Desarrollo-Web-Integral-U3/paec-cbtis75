# Derecho ARCO de Cancelación — DELETE /api/v1/auth/me

Guía del endpoint que permite al titular ejercer su derecho de
**Cancelación** de datos personales bajo la LFPDPPP (Ley Federal de
Protección de Datos Personales en Posesión de los Particulares, México).

## Qué NO hace el endpoint

- **No elimina físicamente la fila** de `users` — rompería FKs históricos
  en `tasks`, `dailies` y `team_members`, lo que dejaría inconsistente
  la información del equipo.
- **No borra las tareas ni dailies** que el usuario haya capturado.

## Qué SÍ hace

Estrategia: **soft-delete con anonimización**. Reescribe los campos con
información personal identificable (PII) a placeholders únicos por id,
sin tocar la clave primaria.

| Campo | Antes | Después |
|---|---|---|
| `nombre_completo` | `"Juan Pérez"` | `"Usuario eliminado"` |
| `email` | `"juan@cbtis75.edu.mx"` | `"eliminado+42@paec.local"` |
| `numero_control` | `"21380001"` | `"ELIM-42"` |
| `password_hash` | `$2b$12$...` (hash del password real) | `$2b$12$...` (hash de una cadena random no reversible) |
| `fecha_anonimizacion` | `NULL` | `2026-08-04T12:34:56` (UTC) |
| `id` | `42` | `42` (no cambia — preserva integridad) |
| `rol` | `estudiante` | `estudiante` (se conserva; no es PII) |
| `consentimiento_privacidad` / `fecha_consentimiento` | `True / 2026-...` | igual (evidencia auditable de consentimiento previo) |

## Contrato del endpoint

```
DELETE /api/v1/auth/me
Authorization: Bearer <jwt_del_titular>

→ 204 No Content   (sin body)
→ 401 Unauthorized (sin token, token inválido, o cuenta ya anonimizada)
```

## Invalidación de sesión

`core/dependencies.get_current_user` verifica en cada request:

```python
if user.fecha_anonimizacion is not None:
    raise credentials_exception  # 401
```

Efecto: cualquier **JWT emitido antes** del DELETE queda inservible al
instante siguiente, **sin necesidad de mantener una blacklist externa**.
El estado vive en la propia BD.

## Preservación de integridad referencial

Después del DELETE se garantiza:

- `SELECT * FROM tasks WHERE asignado_a = <id>` sigue devolviendo las
  mismas filas.
- `SELECT * FROM dailies WHERE user_id = <id>` sigue devolviendo las
  mismas filas.
- `SELECT * FROM team_members WHERE user_id = <id>` sigue devolviendo las
  mismas filas.

Cubierto por el test automatizado
`test_delete_me_preserva_tasks_y_dailies` en `test_auth.py`.

## Cómo se dispara desde el frontend

Página **`/perfil`** (`src/pages/Perfil.jsx`):

1. Muestra los datos actuales del usuario (`GET /me`).
2. Botón rojo **"Eliminar mi cuenta"** al final.
3. `window.confirm` con explicación de qué se preserva y qué no.
4. Si el usuario confirma → `DELETE /me` → 204 → logout local
   (`authStore.logout()`) → redirect a `/login` con mensaje.

## Cómo probarlo manualmente

```bash
# 1. Registrar un usuario nuevo
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "nombre_completo": "Test ARCO",
    "numero_control": "77777777",
    "email": "arco@cbtis75.edu.mx",
    "password": "MiClave@2026",
    "consentimiento_privacidad": true
  }'

# 2. Login para obtener JWT
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"arco@cbtis75.edu.mx","password":"MiClave@2026"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Confirmar identidad (opcional)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Ejercer ARCO
curl -X DELETE http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  -i    # -i para ver los headers y confirmar 204

# 5. Verificar en BD que los datos fueron anonimizados
docker compose exec db psql -U paec_user -d paec_db -c \
  "SELECT id, nombre_completo, email, numero_control, fecha_anonimizacion \
   FROM users WHERE email LIKE 'eliminado+%';"

# 6. Confirmar que el mismo JWT ya NO funciona
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN" \
  -i    # debe responder 401
```

## Tests automatizados que respaldan el comportamiento

En `backend/app/tests/test_auth.py`:

- `test_delete_me_anonimiza_datos_personales` — cumple criterio 1
  (deja de mostrar datos personales identificables).
- `test_delete_me_preserva_tasks_y_dailies` — cumple criterio 2
  (tasks/dailies siguen existiendo sin errores).
- `test_delete_me_sin_token_retorna_401` — seguridad básica.
- `test_token_de_usuario_anonimizado_es_rechazado` — la sesión previa
  queda invalidada.
- `test_get_me_devuelve_datos_del_usuario_autenticado` — GET /me básico
  usado por la página `/perfil`.

## Consideraciones para producción

- **Alembic**: como este cambio agrega la columna `fecha_anonimizacion`,
  en un ambiente con datos reales hay que generar la migración
  correspondiente. En dev basta con `docker compose down -v` para
  recrear el volumen.
- **Bitácora**: cada anonimización queda registrada en logs vía
  `logging.info` en `services/user_arco_service.py`. Recomendable
  encajarlo en el sistema de auditoría cuando se implemente.
- **Frontend**: la página `/perfil` usa `window.confirm` por KISS. Para
  producción conviene un modal más pulido con re-autenticación
  (re-ingresar password antes de aceptar la eliminación) para prevenir
  ataques CSRF vía token robado.
