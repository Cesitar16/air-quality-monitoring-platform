# 05 - Despliegue con Docker

## Descripción general

Este documento explica cómo se construye y levanta el proyecto usando Docker y Docker Compose.

La solución actual utiliza dos servicios:

- `db`: contenedor PostgreSQL 16
- `api`: contenedor FastAPI con Uvicorn

La idea es que ambos servicios puedan iniciarse juntos con un solo comando y queden listos para pruebas locales.

## Archivos involucrados

### `docker-compose.yml`

Define los servicios principales del proyecto:

- construcción y ejecución de la API
- ejecución de PostgreSQL
- variables de entorno
- puertos expuestos
- volumen persistente para la base de datos
- orden de inicialización mediante `depends_on` y `healthcheck`

### `api/Dockerfile`

Define cómo se construye la imagen de la API.

Pasos principales:

1. Usa `python:3.12-slim` como imagen base.
2. Define `/app` como directorio de trabajo.
3. Copia `requirements.txt`.
4. Instala dependencias con `pip`.
5. Copia la carpeta `app/`.
6. Expone el puerto `8000`.
7. Ejecuta Uvicorn con:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Estructura del despliegue

```text
Docker Compose
├── db  -> PostgreSQL 16
└── api -> FastAPI + Uvicorn
```

Relación entre servicios:

```text
PostgreSQL
    ↓
FastAPI
    ↓
Swagger / Dashboard / ETL / Notebooks
```

## Inicialización de la base de datos

El servicio `db` usa la imagen oficial de PostgreSQL 16.

Durante la primera creación del volumen, PostgreSQL ejecuta automáticamente los archivos montados en `/docker-entrypoint-initdb.d/`.

En este proyecto se cargan en este orden:

1. `db/schema.sql`
2. `db/seed_calidad_aire_01_InviernoTemprano.sql`
3. `db/seed_calidad_aire_02_inviernoIIntenso.sql`
4. `db/seed_calidad_aire_03_primavera.sql`

Eso se define en `docker-compose.yml` con nombres prefijados:

```yaml
- ./db/schema.sql:/docker-entrypoint-initdb.d/01_schema.sql
- ./db/seed_calidad_aire_01_InviernoTemprano.sql:/docker-entrypoint-initdb.d/02_seed_01.sql
- ./db/seed_calidad_aire_02_inviernoIIntenso.sql:/docker-entrypoint-initdb.d/03_seed_02.sql
- ./db/seed_calidad_aire_03_primavera.sql:/docker-entrypoint-initdb.d/04_seed_03.sql
```

## Persistencia de datos

La base de datos usa un volumen de Docker:

```yaml
volumes:
  postgres_data:
```

Eso significa que los datos permanecen aunque el contenedor se detenga o se elimine.

Importante:

- si cambias `schema.sql` o alguna seed, PostgreSQL no volverá a ejecutarlos automáticamente mientras el volumen exista
- para reinicializar desde cero, debes eliminar el volumen

Comando:

```bash
docker compose down -v
```

## Variables de entorno

La API y la base usan estas variables:

```env
POSTGRES_DB=calidad_aire_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/calidad_aire_db
```

La API usa `POSTGRES_HOST=db` porque dentro de Docker Compose el contenedor PostgreSQL se resuelve por el nombre del servicio.

## Puertos expuestos

### Base de datos

```text
localhost:5432
```

### API

```text
http://localhost:8000
```

### Swagger

```text
http://localhost:8000/docs
```

## Cómo construir y levantar el proyecto

### 1. Crear `.env`

Si todavía no existe:

```bash
cp .env.example .env
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

### 2. Construir y levantar todo

```bash
docker compose up --build
```

Esto hace lo siguiente:

- construye la imagen de la API usando `api/Dockerfile`
- levanta PostgreSQL
- espera a que PostgreSQL esté saludable
- levanta la API

### 3. Levantar en segundo plano

```bash
docker compose up --build -d
```

## Cómo levantar solo la base de datos

```bash
docker compose up db
```

O en segundo plano:

```bash
docker compose up -d db
```

## Cómo reconstruir solo la API

Si cambias código Python o dependencias:

```bash
docker compose up --build api
```

## Cómo ver logs

### Logs de toda la solución

```bash
docker compose logs
```

### Logs de la API

```bash
docker compose logs api
```

### Logs de PostgreSQL

```bash
docker compose logs db
```

### Seguir logs en tiempo real

```bash
docker compose logs -f api
docker compose logs -f db
```

## Cómo detener los servicios

```bash
docker compose down
```

Si además quieres borrar el volumen de PostgreSQL:

```bash
docker compose down -v
```

## Validación esperada después del despliegue

Si todo levantó correctamente, deberías poder comprobar lo siguiente:

### Healthcheck API

```bash
curl http://localhost:8000/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "air-quality-api",
  "database": "connected"
}
```

### Swagger

Abrir:

```text
http://localhost:8000/docs
```

## Problemas comunes

### Puerto 5432 ocupado

Si PostgreSQL local ya está usando el puerto `5432`, Docker puede fallar al levantar `db`.

Opciones:

- detener el PostgreSQL local
- cambiar el mapeo de puerto en `docker-compose.yml`

### Puerto 8000 ocupado

Si otra app usa el puerto `8000`, la API no podrá exponerse.

Opciones:

- detener el proceso que ocupa ese puerto
- cambiar el mapeo en `docker-compose.yml`

### Cambié el schema o seeds y no veo cambios

Eso normalmente ocurre porque el volumen `postgres_data` sigue existiendo.

Solución:

```bash
docker compose down -v
docker compose up --build
```

### La API no inicia porque la base no está lista

El `docker-compose.yml` ya incluye:

- `healthcheck` en PostgreSQL
- `depends_on` con condición `service_healthy`

Eso ayuda a que la API espere a la base antes de iniciar.

## Resumen

El despliegue del proyecto está pensado para ser simple:

- PostgreSQL se inicializa con `schema.sql` y las seeds
- FastAPI se construye desde `api/Dockerfile`
- Docker Compose coordina ambos servicios
- la API queda expuesta en `localhost:8000`
- Swagger queda disponible en `localhost:8000/docs`
