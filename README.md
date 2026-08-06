# PAEC — Gestión de Proyectos Escolares (CBTis75)

Sistema web/móvil (PWA) para gestionar proyectos ABP bajo la metodología
Scrum + Design Sprint de Google. Caso B de la Actividad de Recuperación 1,
Unidad 3 — ING. Desarrollo y Gestión de Software.

## Diagrama de arquitectura

```
┌─────────────────────┐        HTTPS / JSON        ┌──────────────────────┐
│   FrontEnd (React)  │  ────────────────────────► │   BackEnd (FastAPI)  │
│   Vite + PWA        │  ◄──────────────────────── │   Python 3.12        │
│   Puerto 5173       │                            │   Puerto 8000        │
└─────────────────────┘                            └──────────┬───────────┘
                                                              │ SQLAlchemy
                                                              ▼
                                                      ┌──────────────────────┐
                                                      │   PostgreSQL 16      │
                                                      │   Puerto 5432        │
                                                      └──────────────────────┘

FrontEnd  → nginx (imagen de producción) sirviendo el build estático + service worker (PWA)
BackEnd   → Uvicorn + FastAPI, arquitectura en capas:
            routers → services → repositories → models (SQLAlchemy)
            + factories (notificaciones) + strategies (alertas)
```

## En producción

| Servicio | URL pública |
|---|---|
| FrontEnd (Cloudflare Pages) | https://paec-cbtis75.pages.dev _(placeholder — actualizar tras primer deploy)_ |
| BackEnd  (Railway)          | https://paec-backend-production.up.railway.app _(placeholder)_ |
| BackEnd Swagger UI          | `<backend>/docs` |

Arquitectura de despliegue:

```
GitHub main branch
│
├── Railway  (auto-deploy nativo desde GitHub)
│     ├── PostgreSQL 16 (plugin managed, cifrado at-rest)
│     └── Backend FastAPI (Dockerfile de /backend)
│
├── Cloudflare Pages  (auto-deploy nativo desde GitHub)
│     └── Frontend Vite  (build estático, HTTPS + CDN)
│
└── GitHub Actions
      ├── ci.yml           : lint + pytest + build en cada PR
      ├── cd.yml           : smoke test post-deploy (health check)
      └── alerts-daily.yml : cron diario 08:00 CDMX (POST /cron/evaluar-alertas)
```

**Guía completa de despliegue** paso a paso (crear proyectos en Railway y Cloudflare, configurar variables, sembrar la BD, rotar secretos): [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Ejecutar el proyecto localmente (con Docker)

1. Clonar el repositorio y entrar a la carpeta:
   ```bash
   git clone https://github.com/<usuario>/paec-cbtis75.git
   cd paec-cbtis75
   ```
2. Copiar las variables de entorno de ejemplo:
   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env
   ```
3. Editar `backend/.env` y poner un `JWT_SECRET_KEY` real (nunca dejar el de ejemplo).
4. Levantar todo el entorno con un solo comando:
   ```bash
   docker compose up --build
   ```
5. Servicios disponibles:
   - FrontEnd: http://localhost:5173
   - BackEnd (Swagger/OpenAPI): http://localhost:8000/docs
   - PostgreSQL: localhost:5432

6. **Poblar la BD con datos de demostración (seed):**
   ```bash
   docker compose exec backend python -m app.scripts.seed
   ```
   Es idempotente — se puede correr varias veces sin duplicar registros.
   Deja el sistema listo para una demo completa: 4 usuarios (uno por cada rol),
   un equipo, un sprint activo, 7 tareas, un día de Design Sprint y un daily.

## Credenciales de prueba (creadas por el seed)

Contraseña común para todos los usuarios de demo: **`Demo1234!`**

| Rol           | Correo                       |
|---------------|------------------------------|
| Docente       | docente@cbtis75.edu.mx       |
| Scrum Master  | scrummaster@cbtis75.edu.mx   |
| Estudiante 1  | estudiante1@cbtis75.edu.mx   |
| Estudiante 2  | estudiante2@cbtis75.edu.mx   |

## Flujo de trabajo Git (GitFlow)

- `main`: código en producción. Prohibido push directo.
- `develop`: integración de features antes de liberar a producción. Prohibido push directo.
- `feature/<nombre>`: una rama por persona. Se fusiona a `develop` vía Pull Request, con al menos una aprobación y CI en verde.

## Patrones de diseño implementados (BackEnd)

1. **Repository** — `app/repositories/`
2. **Factory** — `app/factories/notification_factory.py`
3. **Singleton** — `app/core/config.py` (settings) y `app/core/database.py` (engine)
4. **Dependency Injection** — nativo de FastAPI, `app/core/dependencies.py`
5. **Strategy** — `app/strategies/alert_strategy.py`

## Endpoints principales (ver documentación completa en `/docs`)

| Método | Endpoint | Descripción |
|---|---|---|
| POST | /api/v1/auth/register | Registro de usuario |
| POST | /api/v1/auth/login | Login (devuelve JWT) |
| POST | /api/v1/equipo/ | Crear equipo + roles |
| GET  | /api/v1/equipo/{id} | Detalle de equipo |
| POST | /api/v1/design-sprint/ | Planear un día del Design Sprint |
| POST | /api/v1/design-sprint/{id}/evidencia | Subir evidencia de un día |
| POST | /api/v1/design-sprint/{id}/feedback | Comentario del docente |
| POST | /api/v1/sprint | Crear Sprint (parcial) |
| POST | /api/v1/sprint/{id}/aprobar | Docente aprueba el Sprint |
| POST | /api/v1/historia | Crear historia de usuario |
| GET  | /api/v1/historia/equipo/{id}/kanban | Ver tablero Kanban |
| PATCH| /api/v1/historia/{id}/mover | Mover tarea en el Kanban |
| PATCH| /api/v1/historia/{id}/aprobar | Scrum Master aprueba evidencia |
| POST | /api/v1/daily/ | Registrar daily |
| GET  | /api/v1/equipo/{id}/dashboard | Dashboard de avance |
| POST | /api/v1/equipo/{id}/evaluar-alertas | Disparar evaluación de alertas |
