# Guía de puesta en marcha — PAEC

Instrucciones paso a paso para levantar el proyecto por primera vez después
de clonar el repositorio. Sigue el orden **exactamente**.

---

## 1. Prerrequisitos

Antes de tocar cualquier comando del proyecto:

- **Git** instalado (ya lo usaste para clonar).
- **Docker Desktop** instalado **y corriendo**. En Windows, verifícalo
  viendo el ícono de la ballenita en la barra de tareas: debe estar fijo,
  no animado. Si no está instalado, descárgalo de
  https://www.docker.com/products/docker-desktop/.
- **Python** local (opcional, solo lo usamos una vez para generar un
  secret aleatorio). Si no lo tienes, puedes usar cualquier cadena random
  larga.

> No necesitas instalar Node, PostgreSQL, ni Python del proyecto en tu
> máquina. Todo corre dentro de contenedores Docker.

---

## 2. Clonar el proyecto (si no lo has hecho)

```cmd
git clone https://github.com/<usuario>/paec-cbtis75.git
cd paec-cbtis75
```

Todos los siguientes comandos se ejecutan **parado en la raíz del repo**
(donde está el `docker-compose.yml`).

---

## 3. Preparar variables de entorno

Copiar los archivos de ejemplo:

```cmd
copy backend\.env.example backend\.env
copy frontend\.env.example frontend\.env
```

Esto crea `backend\.env` y `frontend\.env` a partir de los templates que
están versionados en el repo.

---

## 4. Generar tu `JWT_SECRET_KEY`

El archivo `backend\.env` tiene un placeholder para la llave JWT. **NO
dejes el valor de ejemplo** — cámbialo por uno aleatorio.

### Opción A: con Python

```cmd
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

(si `python3` no funciona, prueba `python`).

Copia la cadena que imprime.

### Opción B: sin Python

Usa cualquier cadena aleatoria de al menos 32 caracteres. Ejemplo válido:

```
k8Jx2mN9pQ4rT7vW1yZ3aB6cE9fH2iL5oP8sV1xA4dG7jM0nR3uY6bE9hK2mQ5tW
```

### Pegar el valor en el `.env`

Abre el archivo con Notepad:

```cmd
notepad backend\.env
```

Busca la línea:

```
JWT_SECRET_KEY=cambia_esto_por_una_llave_larga_y_aleatoria
```

Y déjala con tu valor generado:

```
JWT_SECRET_KEY=<tu_cadena_aleatoria>
```

Guarda y cierra el editor.

---

## 5. Levantar los servicios con Docker

Un solo comando enciende la base de datos, el backend y el frontend:

```cmd
docker compose up --build -d
```

- `--build` fuerza a construir las imágenes (necesario la primera vez).
- `-d` corre en segundo plano y te libera la terminal.

La primera vez tarda **3–5 minutos** porque baja imágenes de Python, Node,
Postgres y nginx.

### Verificar que los 3 servicios estén arriba

```cmd
docker compose ps
```

Deberías ver algo así (todos con `Up`):

```
NAME                       STATUS
paec-cbtis75-db-1          Up (healthy)
paec-cbtis75-backend-1     Up
paec-cbtis75-frontend-1    Up
```

---

## 6. Poblar la base de datos con datos de demo (seed)

```cmd
docker compose exec backend python -m app.scripts.seed
```

El script imprime al final un resumen con las credenciales generadas.
Es **idempotente**: puedes correrlo varias veces sin duplicar datos.

**Credenciales para la demo** (todas con la misma contraseña
`Demo1234!`):

| Rol           | Correo                       |
|---------------|------------------------------|
| Docente       | docente@cbtis75.edu.mx       |
| Scrum Master  | scrummaster@cbtis75.edu.mx   |
| Estudiante 1  | estudiante1@cbtis75.edu.mx   |
| Estudiante 2  | estudiante2@cbtis75.edu.mx   |

---

## 7. Correr los tests (opcional pero recomendado)

Para confirmar que todo quedó bien instalado:

```cmd
docker compose exec backend pytest -v
```

Debes ver **10 passed** en verde.

---

## 8. Abrir la aplicación

- **Frontend**: http://localhost:5173/login
- **Backend (Swagger/OpenAPI)**: http://localhost:8000/docs
- **PostgreSQL**: `localhost:5432` (usuario `paec_user`, password `paec_pass`,
  base `paec_db`)

Entra con cualquier correo del paso 6 y contraseña `Demo1234!`.

---

## 9. Comandos útiles del día a día

Una vez que ya lo tienes corriendo:

```cmd
:: Detener todos los servicios (mantiene los datos)
docker compose down

:: Detener y BORRAR datos de la BD (vuelve a estado limpio)
docker compose down -v

:: Volver a levantar sin reconstruir imágenes
docker compose up -d

:: Ver logs en tiempo real
docker compose logs -f backend
docker compose logs -f frontend

:: Reconstruir solo un servicio (después de tocar código)
docker compose up -d --build backend

:: Conectarse a la BD con psql
docker compose exec db psql -U paec_user -d paec_db
```

---

## 10. Solución de problemas comunes

### `docker daemon is not running`
Docker Desktop no está abierto. Ábrelo desde el menú Inicio y espera a
que la ballenita en la barra de tareas quede fija.

### `port already in use` (5173, 8000 o 5432)
Otro proceso está usando ese puerto. Ciérralo o cambia el mapeo en
`docker-compose.yml` (por ejemplo, `"5174:80"` para el frontend).

### `No module named 'secrets'` al ejecutar Python
Tienes Python 2 como default. Usa `python3` en vez de `python`.

### `ImportError: email-validator is not installed` en el backend
Estás en una versión vieja del código. Haz `git pull` y rebuild:
```cmd
docker compose up -d --build backend
```

### `"clientsClaim" is not exported by workbox-core` al construir el frontend
Tu carpeta local `frontend/node_modules` está contaminada. Bórrala y
reconstruye sin cache:
```cmd
rmdir /s /q frontend\node_modules
rmdir /s /q frontend\.vite
docker compose build --no-cache frontend
docker compose up -d
```

### El frontend carga pero no aparece la pantalla de registro
El `<nav>` no tiene link a `/register`. Ve directo a la URL:
http://localhost:5173/register

### Quiero empezar desde cero (BD vacía)
```cmd
docker compose down -v
docker compose up --build -d
docker compose exec backend python -m app.scripts.seed
```

---

## Flujo de trabajo Git

Este repo usa **GitFlow**:

- `main` — código en producción (prohibido push directo).
- `develop` — integración antes de liberar (prohibido push directo).
- `feature/<tu-nombre>` — tu rama personal. Se fusiona a `develop` vía
  Pull Request con al menos una aprobación y CI en verde.

Crear tu rama:

```cmd
git checkout develop
git pull origin develop
git checkout -b feature/<tu-nombre>
```

Al terminar cambios: `commit` → `push origin feature/<tu-nombre>` → abrir
PR hacia `develop` en GitHub.
