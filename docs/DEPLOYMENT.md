# Despliegue a producción — PAEC

Guía paso a paso para desplegar el sistema PAEC en la nube. Usa
**Railway** para el backend + PostgreSQL y **Cloudflare Workers Builds**
(sucesor de Cloudflare Pages) para el frontend. Ambos servicios se
auto-actualizan al hacer merge a `main` mediante la integración nativa
con GitHub (webhook implícito). Sobre eso, GitHub Actions ejecuta un
**smoke test** post-deploy (`cd.yml`) que deja evidencia visible del
despliegue exitoso.

## URLs en producción

| Servicio | URL |
|---|---|
| Frontend (Cloudflare) | https://paec-cbtis75.f51783154.workers.dev |
| Backend (Railway) | https://paec-cbtis75-production.up.railway.app |
| Swagger / OpenAPI | https://paec-cbtis75-production.up.railway.app/docs |
| Health check | https://paec-cbtis75-production.up.railway.app/api/v1/health |

## Arquitectura de producción

```
     Usuario (navegador)
             │  HTTPS
             ▼
  ┌──────────────────────────┐        HTTPS + JWT
  │  Cloudflare Pages         │   ─────────────────►   ┌────────────────────────┐
  │  Frontend (Vite build)    │                        │  Railway (Docker)       │
  │  paec-cbtis75.pages.dev   │   ◄─────────────────   │  Backend (FastAPI)      │
  └──────────────────────────┘        JSON             │  paec-backend-...       │
                                                       │  .up.railway.app        │
                                                       └───────────┬────────────┘
                                                                   │ psycopg2
                                                                   ▼
                                                       ┌────────────────────────┐
                                                       │  Railway (PostgreSQL)   │
                                                       │  Plugin managed         │
                                                       │  cifrado at-rest        │
                                                       └────────────────────────┘

GitHub main branch  →  push  →  Railway rebuild + deploy   (backend + DB link)
                            →   Cloudflare Pages rebuild + deploy (frontend)
                            →   GitHub Actions cd.yml smoke test  (verificacion)
```

## Prerrequisitos

- Cuenta en https://railway.app (login con GitHub, gratis, 500 hrs/mes de compute).
- Cuenta en https://cloudflare.com (Pages ilimitado, 500 builds/mes gratis).
- Repositorio en GitHub con la rama `main` como estable.

---

## Fase 1 — Backend + PostgreSQL en Railway

### 1.1 Crear el proyecto

1. Ir a https://railway.app y **Login with GitHub**.
2. **New Project** → **Deploy from GitHub repo** → seleccionar `paec-cbtis75`.
3. Railway pregunta qué rama seguir → **`main`** (default).

### 1.2 Configurar el servicio backend

Railway detecta que el repo es un monorepo (backend + frontend). Hay que
apuntarlo al subdirectorio correcto:

1. En el servicio recién creado, **Settings** → **Source** →
   **Root Directory**: `backend`
2. **Settings** → **Build** → confirmar **Dockerfile Path**: `Dockerfile`
   (Railway auto-detecta el `backend/Dockerfile`).
3. **Settings** → **Networking** → **Generate Domain** para obtener una
   URL pública tipo `paec-backend-production.up.railway.app`.
4. **Anotar esa URL** — la necesitaremos en Cloudflare y en GitHub Secrets.

### 1.3 Agregar PostgreSQL

1. En el mismo proyecto, botón **+ Create** → **Database** → **Add PostgreSQL**.
2. Railway crea automáticamente el servicio Postgres y expone la variable
   `DATABASE_URL` compartida con el servicio backend.
3. **Nota**: el plugin trae cifrado at-rest incluido (cumple criterio de
   Actividad 1: "Cifrado en reposo").

### 1.4 Variables de entorno del backend

En el servicio backend, **Variables**, agregar (o pegar en batch):

```env
ENVIRONMENT=production
JWT_SECRET_KEY=<generar_uno_nuevo_con_python_-c_import_secrets;print(secrets.token_urlsafe(48))>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# CORS: DEJAR VACIO POR AHORA. Se llena en Fase 3 con la URL de Cloudflare.
CORS_ORIGINS=["https://TU-PROYECTO.pages.dev"]

# Notificaciones (usar los mismos valores que tienes en local para Resend)
NOTIFICATION_PROVIDER=email
EMAIL_API_KEY=re_XXXXXXXXXXXXXXXXXXXXXXXXXXXX
EMAIL_API_URL=https://api.resend.com/emails
EMAIL_FROM=PAEC <onboarding@resend.dev>

# Cloudinary (mismos valores del .env local)
CLOUDINARY_CLOUD_NAME=e4t8zxfu
CLOUDINARY_API_KEY=672512485784651
CLOUDINARY_API_SECRET=6EAHmivhSHpS4QL6GTuYW6io8X4

# Cron secret (mismo del .env local o generar uno nuevo con secrets.token_urlsafe(48))
CRON_SECRET=<mismo_o_nuevo>
```

> `DATABASE_URL` NO se pone manualmente — Railway la inyecta al conectar
> el plugin PostgreSQL en el paso 1.3.

### 1.5 Primer deploy

Railway despliega automáticamente en cuanto guarda la última var. Espera
a que el ícono del servicio se ponga verde (~2 minutos primera vez).

Verificar:

```bash
curl https://TU-BACKEND.up.railway.app/api/v1/health
# → {"status":"ok","environment":"production"}
```

### 1.6 Sembrar la BD (una sola vez)

Instalar la CLI de Railway localmente:

```bash
npm install -g @railway/cli
railway login   # abre el navegador para autenticar
```

Vincular al proyecto y ejecutar el seed dentro del contenedor:

```bash
cd C:\paec-cbtis75
railway link          # selecciona el proyecto PAEC
railway run --service backend python -m app.scripts.seed
```

Al final imprime el resumen con los 4 usuarios de demo listos.

---

## Fase 2 — Frontend en Cloudflare Pages

### 2.1 Crear el proyecto

1. Ir a https://dash.cloudflare.com → **Workers & Pages** → **Create** →
   **Pages** → **Connect to Git**.
2. Autorizar GitHub y seleccionar `paec-cbtis75`.
3. Rama de producción: **`main`**.

### 2.2 Configuración de build

| Campo | Valor |
|---|---|
| Framework preset | **Vite** (auto-detectado) |
| Build command | `npm install && npm run build` |
| Build output directory | `dist` |
| Root directory (advanced) | **`frontend`** |
| Node version | `20` |

### 2.3 Variable de entorno del frontend

En **Settings** → **Environment variables** → **Production**:

```
VITE_API_URL = https://TU-BACKEND.up.railway.app
```

> Sin slash final. Se inyecta en tiempo de `npm run build`.

### 2.4 Primer deploy

Cloudflare compila y despliega automáticamente. Al terminar te da una URL
tipo `paec-cbtis75.pages.dev`. **Anotarla**.

Verificar abriendo la URL en el navegador — deberías ver `/` con la
pantalla de intro.

---

## Fase 3 — Cerrar el círculo: CORS y GitHub Secrets

### 3.1 Actualizar CORS en Railway

Con la URL de Cloudflare del paso 2.4:

1. Railway → servicio backend → **Variables** → editar `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=["https://paec-cbtis75.pages.dev"]
   ```
2. Railway redespliega automáticamente (~1 min).

### 3.2 Agregar el secret a GitHub

1. En el repo → **Settings** → **Secrets and variables** → **Actions** →
   **New repository secret**.
2. Nombre: `BACKEND_URL_PROD`
   Valor: `https://TU-BACKEND.up.railway.app` (sin slash final).

Este secret lo usan dos workflows:
- `cd.yml` para el smoke test post-deploy.
- `alerts-daily.yml` para el cron diario de alertas.

### 3.3 (Opcional) Rotar CRON_SECRET

Si generaste uno nuevo en Railway, actualizar también el secret
`CRON_SECRET` en GitHub para que el cron diario lo mande igual.

---

## Fase 4 — Verificación end-to-end

1. Abrir `https://TU-BACKEND.up.railway.app/docs` → Swagger UI carga.
2. Abrir `https://paec-cbtis75.pages.dev/login` → intentar login con:
   - Email: `docente@cbtis75.edu.mx`
   - Password: `Demo1234!`
3. Debería entrar y mostrar la nav bar.
4. Ir a `/dashboard` (permitido para docente).

Si algo falla:
- Ver logs de Railway → tab **Deployments** → click en el deploy → **View logs**.
- Ver logs de Cloudflare → **Deployments** → click en el build → **View build log**.
- Ver que CORS esté bien configurado (mensaje típico en consola del navegador si falla).

---

## Flujo de trabajo continuo

De aquí en adelante:

1. Cualquier PR contra `develop` o `main` dispara `ci.yml`
   (lint + pytest + build).
2. Al hacer **merge de `develop` en `main`**:
   - Railway detecta el push y despliega el backend automáticamente.
   - Cloudflare Pages detecta el push y despliega el frontend automáticamente.
   - `cd.yml` corre en GitHub Actions y hace smoke test contra
     `/api/v1/health` de Railway — queda evidencia visible en el tab
     Actions.

## Costos y límites

| Servicio | Free tier | Cubre R1 |
|---|---|---|
| Railway | 500 hrs de compute + $5 crédito | Sobrado |
| Cloudflare Pages | Ilimitado en runtime, 500 builds/mes | Sobrado |
| Resend (email) | 3,000/mes, 100/día | Sobrado |
| Cloudinary | 25 GB/mes storage | Sobrado |

Total: **$0/mes** para lo que necesita R1.

## Rotación de secretos

Si se filtra alguno (accidentalmente commiteado, etc.):

- **JWT_SECRET_KEY**: cambiarlo en Railway invalida todos los tokens
  existentes (usuarios tendrán que volver a loguear).
- **CRON_SECRET**: cambiarlo en Railway Y en el secret `CRON_SECRET` de
  GitHub Actions.
- **EMAIL_API_KEY**: revocar la key en el dashboard de Resend y generar
  una nueva.
- **CLOUDINARY_API_SECRET**: en el dashboard de Cloudinary,
  **Settings** → **Security** → **Rotate API secret**.
