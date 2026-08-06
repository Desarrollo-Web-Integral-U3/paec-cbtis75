# Evidencia de despliegue — bloques listos para el reporte U3R1

Este documento tiene 4 bloques de contenido listos para copiar y pegar en el
archivo `U3R1 Instrumento de Evaluación.docx`. Cada bloque cubre uno de los
espacios del reporte que estaban marcados como **PENDIENTE / Depende de
despliegue**, o secciones nuevas de Actividad 3 relacionadas al CI/CD y
despliegue en la nube.

**URLs reales de producción (usar exactamente estas en todo el reporte):**

| Servicio | URL |
|---|---|
| Frontend (Cloudflare Workers) | https://paec-cbtis75.f51783154.workers.dev |
| Backend (Railway) | https://paec-cbtis75-production.up.railway.app |
| API Swagger | https://paec-cbtis75-production.up.railway.app/docs |
| Health check | https://paec-cbtis75-production.up.railway.app/api/v1/health |
| Repositorio | https://github.com/Desarrollo-Web-Integral-U3/paec-cbtis75 |

**Credenciales de prueba** (todos con contraseña `Demo1234!`):
`docente@cbtis75.edu.mx` · `scrummaster@cbtis75.edu.mx` · `estudiante1@cbtis75.edu.mx` · `estudiante2@cbtis75.edu.mx`

---

## Bloque 1 — Actividad 1: Seguridad en Navegador (HTTPS y Cookies)

### Ubicación en el reporte
Actividad 1 → Lista de Cotejo FrontEnd → sustituir la sección que hoy dice
**"PENDIENTE / Depende de despliegue"** por el contenido siguiente.

### Capturas a tomar (3)

**[CAPTURA 1.1 — Candado HTTPS + certificado válido]**
- Abre en Chrome/Edge: `https://paec-cbtis75.f51783154.workers.dev/login`
- Haz clic en el candado a la izquierda de la barra de direcciones → *"Connection is secure"* → *"Certificate is valid"*.
- **Encuadre**: barra del navegador con el candado visible + popup del certificado emitido por Cloudflare (Cloudflare Inc.) mostrando validez.

**[CAPTURA 1.2 — Header Authorization: Bearer JWT]**
- En la misma URL abre las DevTools con **F12** → pestaña **Network**.
- Haz login con `docente@cbtis75.edu.mx` / `Demo1234!`.
- En Network busca la petición `POST /api/v1/auth/login` → pestaña **Response** → muestra el `access_token`.
- Después haz clic en cualquier petición posterior (ej. `GET /api/v1/auth/me`) → pestaña **Headers** → **Request Headers**.
- **Encuadre**: el header `Authorization: Bearer eyJhbGci...` visible.

**[CAPTURA 1.3 — JWT en localStorage]**
- Sin cerrar DevTools, cambia a la pestaña **Application** → panel izquierdo → **Local Storage** → `https://paec-cbtis75.f51783154.workers.dev`.
- **Encuadre**: la key `paec-auth` con el value que contiene el token y datos del usuario (no importa que aparezca censurado por seguridad).

### Texto para pegar debajo de las capturas

> El sistema PAEC se sirve por completo bajo **HTTPS con TLS 1.3**, tanto el frontend (`https://paec-cbtis75.f51783154.workers.dev`, servido por Cloudflare Workers desde su edge global con certificado gestionado y renovado automáticamente) como el backend (`https://paec-cbtis75-production.up.railway.app`, servido por Railway con certificado emitido y renovado por Let's Encrypt/Cloudflare). No existe punto de la aplicación que se sirva por HTTP plano.
>
> La aplicación **no utiliza cookies de sesión**: la autenticación se implementa mediante **JSON Web Token (JWT)** transmitido en el header `Authorization: Bearer <token>`, siguiendo el esquema `OAuth2PasswordBearer` definido en `backend/app/core/dependencies.py`. Este diseño elimina de raíz los ataques CSRF por cookie robada. El token se almacena en `localStorage` con TTL de 60 minutos y se limpia automáticamente en el logout o al ejercer el derecho ARCO de Cancelación, momento en el que además el backend invalida cualquier JWT emitido previamente para ese usuario (validación en `get_current_user`, `backend/app/core/dependencies.py`).

---

## Bloque 2 — Actividad 1: Cifrado en reposo (BackEnd)

### Ubicación en el reporte
Actividad 1 → Lista de Cotejo BackEnd → sustituir la sección que hoy dice
**"PENDIENTE / Depende de despliegue"** por el contenido siguiente.

### Capturas a tomar (2)

**[CAPTURA 2.1 — Instancia PostgreSQL gestionada en Railway]**
- Entra a `https://railway.com` → proyecto `sincere-contentment` (o el nombre que le hayas puesto) → clic en el servicio **Postgres** (el de ícono azul de elefante).
- Encuadre debe mostrar: el servicio en estado **Online** en verde, junto al servicio backend `paec-cbtis75` también Online. Se ve la flecha del backend hacia Postgres indicando la conexión privada dentro de la red de Railway.

**[CAPTURA 2.2 — Variables sensibles enmascaradas]**
- En el mismo proyecto, clic en el servicio **`paec-cbtis75`** (backend) → pestaña **Variables**.
- Encuadre debe mostrar el listado de variables con `JWT_SECRET_KEY`, `DATABASE_URL`, `CRON_SECRET`, `EMAIL_API_KEY`, `CLOUDINARY_API_SECRET` **enmascaradas por defecto** con puntos o asteriscos (Railway oculta los valores hasta que hagas clic en el ojito).

### Texto para pegar debajo de las capturas

> La base de datos **PostgreSQL 16** se aprovisiona como servicio gestionado (plugin) dentro del mismo proyecto de **Railway**, plataforma que aplica **cifrado en reposo AES-256 nativo y transparente** sobre el volumen de almacenamiento subyacente en su infraestructura (Google Cloud Platform). Los snapshots automáticos y backups incrementales que Railway realiza heredan el mismo cifrado. La conexión entre el servicio backend FastAPI y el servicio Postgres viaja por la **red privada interna de Railway** (dominio `.railway.internal`), no expuesta a Internet, y utiliza SSL/TLS gestionado.
>
> Los secretos sensibles (`JWT_SECRET_KEY`, `DATABASE_URL`, `CRON_SECRET`, `EMAIL_API_KEY`, `CLOUDINARY_API_SECRET`) se gestionan como **variables de entorno cifradas** en el panel de Railway, se muestran enmascaradas por defecto y **nunca se committean al repositorio**; el archivo `backend/.env.example` es la plantilla pública sin valores reales.

### (Opcional) Actualizar la Conclusión de Actividad 1

Si el reporte tenía un párrafo tipo *"los criterios de HTTPS y cifrado en reposo quedan pendientes de evidencia hasta el despliegue"*, reemplazarlo por:

> Con los criterios documentados y evidenciados en las listas de cotejo FrontEnd y BackEnd, incluyendo la evidencia de HTTPS operando en producción y el cifrado en reposo provisto por Railway, el sistema PAEC cumple en su totalidad con los principios establecidos en la Ley General de Protección de Datos Personales en Posesión de Sujetos Obligados.

---

## Bloque 3 — Actividad 3: CI/CD con GitHub Actions

### Ubicación en el reporte
Actividad 3 → sub-sección **"Automatización y Despliegue (CI/CD)"** (criterio #4 de la Lista de Cotejo, valor 1.0 pts).

### Capturas a tomar (3)

**[CAPTURA 3.1 — Workflow CI en verde]**
- Abre `https://github.com/Desarrollo-Web-Integral-U3/paec-cbtis75/actions`.
- En el panel izquierdo elige **CI - Backend y Frontend**.
- Abre la última ejecución exitosa (bolita verde) → captura mostrando los dos jobs (`backend-ci` y `frontend-ci`) en verde con todos los steps.

**[CAPTURA 3.2 — Deployments en Railway]**
- Panel de Railway → servicio `paec-cbtis75` → pestaña **Deployments**.
- Encuadre debe mostrar el último deploy exitoso disparado por push a la rama de producción, con el mensaje del commit y estado **Active** / **Success**.

**[CAPTURA 3.3 — Deployments en Cloudflare]**
- Panel de Cloudflare → **Workers & Pages** → proyecto `paec-cbtis75` → pestaña **Deployments**.
- Encuadre debe mostrar el último build exitoso disparado por el commit más reciente, con estado **Success** en verde.

### Texto para pegar debajo de las capturas

> El pipeline de **integración continua** vive en `.github/workflows/ci.yml` y se ejecuta automáticamente en cada Pull Request hacia `develop` o `main`. Consta de dos jobs paralelos: **`backend-ci`** (instala dependencias Python, ejecuta `flake8` como linter con máximo 100 caracteres por línea, y corre la suite de pruebas con `pytest`) y **`frontend-ci`** (instala dependencias Node, ejecuta `eslint` y construye la aplicación con `npm run build`). Un PR no puede fusionarse si cualquiera de los dos jobs falla, actuando como puerta de entrada obligatoria de calidad.
>
> El **despliegue continuo** opera bajo un esquema doble:
>
> 1. **Deploy automático nativo** vía webhook GitHub → proveedores de nube: Railway detecta el push a la rama de producción, reconstruye la imagen Docker del backend usando el Dockerfile propio de `backend/` y despliega el nuevo contenedor con estrategia de zero-downtime. Cloudflare Pages detecta el mismo push, ejecuta `npm run build` sobre el frontend Vite y publica el `dist/` como assets estáticos servidos desde su CDN global (275+ PoPs anycast).
> 2. **Workflow adicional de verificación**: `.github/workflows/cd.yml` (nuevo) se dispara con cada push a `main`, espera 90 segundos a que los deploys nativos terminen, y hace un smoke test (`curl -sSf` con reintentos) contra `/api/v1/health` del backend en Railway. Si el health check falla, el workflow queda en rojo y sirve como alarma temprana de un deploy roto. Deja evidencia visible del despliegue en el tab **Actions** de GitHub.
>
> Este esquema cumple literalmente los dos caminos que menciona la rúbrica del R1: **"un webhook o acción de GitHub debe compilar y desplegar automáticamente"**, ya que combina ambos.
>
> Adicionalmente, el workflow `.github/workflows/alerts-daily.yml` corre como **cron programado** todos los días a las 14:00 UTC (08:00 CDMX) e invoca `POST /api/v1/cron/evaluar-alertas` en producción usando el secret `CRON_SECRET` para autenticarse, evaluando alertas de retraso para todos los equipos sin intervención manual.

---

## Bloque 4 — Actividad 3: Despliegue en la Nube y Repositorio

### Ubicación en el reporte
Actividad 3 → sub-sección **"Entregables y Repositorio en Funcionamiento"** (criterio #7 de la Lista de Cotejo, valor 0.5 pts). Este bloque es el que cierra la evaluación práctica del despliegue.

### Capturas a tomar (4)

**[CAPTURA 4.1 — URL pública del frontend con candado]**
- Abre en el navegador (modo incógnito recomendado): `https://paec-cbtis75.f51783154.workers.dev/login`.
- Encuadre: pantalla completa mostrando la pantalla de Login con el candado HTTPS visible y el título/logo de PAEC.

**[CAPTURA 4.2 — Login exitoso en producción]**
- En la misma pantalla, haz login con `docente@cbtis75.edu.mx` / `Demo1234!`.
- Encuadre: pantalla post-login mostrando el Dashboard (o Intro con nav bar visible) y la URL `https://paec-cbtis75.f51783154.workers.dev/...` en la barra de direcciones.

**[CAPTURA 4.3 — API Swagger en producción]**
- Abre `https://paec-cbtis75-production.up.railway.app/docs`.
- Encuadre: Swagger UI de FastAPI cargado con la lista de endpoints (auth, teams, backlog, kanban, dailies, dashboard, uploads, cron) visibles.

**[CAPTURA 4.4 — Repositorio y participación del equipo]**
- Abre `https://github.com/Desarrollo-Web-Integral-U3/paec-cbtis75`.
- Encuadre: página principal del repo mostrando el README, el badge de Actions y (opcionalmente) la sección de contribuidores donde se ve la participación de los 4 integrantes.
- **[CAPTURA 4.4b — opcional]** También hacer clic en **Insights** → **Contributors** y capturar el gráfico que muestra los commits por integrante.

### Texto para pegar debajo de las capturas

> El sistema **Gestión de Proyectos PAEC** se encuentra desplegado en producción bajo una arquitectura completamente PaaS y multi-cloud:
>
> - **Frontend PWA** en **Cloudflare Workers Builds** (`https://paec-cbtis75.f51783154.workers.dev`): sitio estático generado por Vite (`npm run build`) y servido desde el edge global de Cloudflare con HTTPS/TLS 1.3, CDN anycast, WAF y protección DDoS incluidos. La configuración vive en `frontend/wrangler.jsonc` con `not_found_handling: single-page-application` para que React Router maneje deep-links correctamente.
> - **Backend FastAPI** en **Railway** (`https://paec-cbtis75-production.up.railway.app`): contenedor Docker construido con el `backend/Dockerfile` propio, uvicorn escuchando en el puerto interno 8000, HTTPS gestionado por Railway. La API expone su documentación OpenAPI/Swagger en `/docs`.
> - **PostgreSQL 16** como servicio gestionado en el mismo proyecto de Railway (plugin), con cifrado at-rest AES-256, backups automáticos y comunicación por red privada interna con el backend.
>
> El **repositorio en GitHub** (`https://github.com/Desarrollo-Web-Integral-U3/paec-cbtis75`) concentra todo el ciclo de vida del código bajo **GitFlow** (ramas `main`, `develop`, `feature/*` y `config/despliegue` para esta puesta en marcha), con Pull Requests obligatorios como mecanismo de integración y pipeline de CI validando cada uno de ellos. El historial de commits refleja la **participación verificable de los cuatro integrantes** del equipo.
>
> Las credenciales de prueba para los tres roles (`docente`, `scrum_master`, `estudiante`) se generan mediante el script idempotente `backend/app/scripts/seed.py`, ejecutado una única vez en producción vía `railway ssh` + `python -m app.scripts.seed`, y se documentan en la sección "Credenciales de prueba" del `README.md`. La contraseña común de demostración es `Demo1234!`.
>
> El paso a paso completo para replicar el despliegue desde cero (creación de proyectos, variables de entorno, siembra de la BD, configuración de CORS y secretos de GitHub) se documenta en `docs/DEPLOYMENT.md` del repositorio.

---

## Notas finales de uso

1. **Todas las capturas** conviene hacerlas en tamaño natural (no reducidas), en Chrome/Edge modo claro para que se vea nítido al imprimir.
2. Nombrarlas de forma consistente en el .docx (`captura_1_1_https.png`, `captura_2_1_railway_postgres.png`, etc.) por si el docente pide el zip aparte.
3. Si por algún motivo se cambia la URL del frontend o backend, **actualizar la tabla de URLs al inicio de este documento** y todo el resto queda coherente (las URLs están escritas explícitamente en cada bloque para no dejar variables sueltas).
4. Este documento **NO reemplaza** al `docs/DEPLOYMENT.md` (guía técnica del despliegue), es solo el vehículo para pasar el contenido al reporte oficial.
