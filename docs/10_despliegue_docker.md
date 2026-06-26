# 10 - Despliegue con Docker

## Objetivo

Este documento define el contrato Docker vigente del proyecto. La regla actual es simple:

- un solo `docker-compose.yml` en la raiz
- los Dockerfiles viven en `docker/`
- no se mantiene un compose duplicado dentro de subcarpetas

## Componentes que se despliegan

La solucion contenedorizada considera estos servicios:

- `db`: PostgreSQL 16 con schema y seeds del caso
- `api`: FastAPI + Uvicorn
- `dashboard`: Streamlit opcional, activado por profile

## Archivos involucrados

- `docker-compose.yml`: orquestacion oficial
- `docker/api.Dockerfile`: build de la API desde contexto raiz
- `docker/dashboard.Dockerfile`: build opcional del dashboard
- `db/schema.sql`: schema inicial
- `db/seed_calidad_aire_01_InviernoTemprano.sql`
- `db/seed_calidad_aire_02_inviernoIIntenso.sql`
- `db/seed_calidad_aire_03_primavera.sql`

## Estructura del despliegue

```text
docker-compose.yml
        |
        +-- db        -> PostgreSQL 16
        +-- api       -> FastAPI
        +-- dashboard -> Streamlit (profile opcional)
```

Relacion funcional:

```text
PostgreSQL
    ->
API FastAPI
    ->
ETL / notebooks / modelamiento / Swagger

Artefactos locales
    ->
Dashboard Streamlit
```

## Inicializacion de la base

En la primera creacion del volumen `postgres_data`, PostgreSQL ejecuta automaticamente los archivos montados en `/docker-entrypoint-initdb.d/`.

Orden actual:

1. `db/schema.sql`
2. `db/seed_calidad_aire_01_InviernoTemprano.sql`
3. `db/seed_calidad_aire_02_inviernoIIntenso.sql`
4. `db/seed_calidad_aire_03_primavera.sql`

Si luego cambias schema o seeds, esos cambios no se reaplican mientras el volumen siga existiendo.

Para reinicializar desde cero:

```powershell
docker compose down -v
docker compose up --build
```

## Variables de entorno principales

```env
POSTGRES_DB=calidad_aire_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/calidad_aire_db
```

Dentro de Compose, la API resuelve la base con `POSTGRES_HOST=db` porque `db` es el nombre del servicio.

## Puertos expuestos

- Base de datos: `localhost:5432`
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Dashboard opcional: `http://localhost:8501`

## Comandos oficiales

Levantar base de datos y API:

```powershell
docker compose up --build
```

Levantar tambien el dashboard:

```powershell
docker compose --profile dashboard up --build
```

Levantar en segundo plano:

```powershell
docker compose up --build -d
docker compose --profile dashboard up --build -d
```

Reconstruir solo la API:

```powershell
docker compose up --build api
```

Levantar solo la base:

```powershell
docker compose up -d db
```

## Logs y diagnostico

Logs de toda la solucion:

```powershell
docker compose logs
```

Logs por servicio:

```powershell
docker compose logs api
docker compose logs db
docker compose logs dashboard
```

Seguimiento en tiempo real:

```powershell
docker compose logs -f api
docker compose logs -f db
```

## Detencion

```powershell
docker compose down
```

Con borrado de volumen:

```powershell
docker compose down -v
```

## Validacion esperada

Una vez levantados `db` y `api`, deberias poder validar:

```powershell
curl http://localhost:8000/health
```

Y abrir:

- `http://localhost:8000/docs`

Si activaste el profile del dashboard:

- `http://localhost:8501`

## Consideraciones del dashboard

El dashboard no recalcula ETL ni modelos al iniciar. Solo lee artefactos ya generados, por ejemplo:

- `data/processed/dataset_modelado.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/metricas_regresion.json`
- `models/regression/modelo_mp25_24h.joblib`

Por eso, antes de construir la imagen del dashboard, conviene haber ejecutado ETL, clustering y regresion al menos una vez.

## Problemas comunes

### El puerto 5432 esta ocupado

Cierra PostgreSQL local o cambia el mapeo del servicio `db`.

### El puerto 8000 esta ocupado

Cierra el proceso que lo usa o cambia el puerto expuesto de `api`.

### El dashboard abre pero no muestra datos actualizados

Normalmente significa que los artefactos de `data/processed/` o `models/` no fueron regenerados antes del build.

### Cambie una seed y no veo cambios

Eso ocurre porque el volumen `postgres_data` conserva el estado previo. Reinicializa con `docker compose down -v`.

## Resumen

La convencion final queda asi:

- Compose oficial: `docker-compose.yml` en raiz
- Dockerfiles oficiales: `docker/`
- Base y API: flujo principal contenedorizado
- Dashboard: servicio opcional por profile, sin duplicar compose
