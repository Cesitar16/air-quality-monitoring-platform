# Monitoreo de Calidad del Aire

API REST construida con FastAPI y PostgreSQL para una evaluación universitaria. El proyecto usa el archivo existente `schema_seed.sql` para crear la base de datos, poblarla con datos de prueba y generar las vistas usadas por la API.

## Estructura del proyecto

```text
.
├── api
│   ├── app
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routes
│   │       ├── comunas.py
│   │       ├── estaciones.py
│   │       ├── industrias.py
│   │       └── monitoreo.py
│   ├── Dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── .env.example
├── README.md
└── schema_seed.sql
```

## Cómo levantar el proyecto

1. Crear el archivo `.env` a partir del ejemplo:

```bash
cp .env.example .env
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Levantar PostgreSQL y FastAPI:

```bash
docker compose up --build
```

3. Abrir la API en:

- `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Servicios Docker

- `db`: PostgreSQL 16
- `api`: FastAPI con Uvicorn

## Variables de entorno

```env
POSTGRES_DB=calidad_aire_db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/calidad_aire_db
```

## Endpoints disponibles

### Health

- `GET /`
- `GET /health`

### Comunas

- `GET /comunas`
- `GET /comunas/{id_comuna}`

### Estaciones

- `GET /estaciones`
- `GET /estaciones/{id_estacion}`

### Industrias

- `GET /industrias`
- `GET /industrias/{id_industria}`

### Monitoreo

- `GET /monitoreo`
- `GET /monitoreo/{id_monitoreo}`
- `POST /monitoreo`

Filtros opcionales para `GET /monitoreo`:

- `comuna`
- `region`
- `nivel_riesgo`
- `fecha_inicio`
- `fecha_fin`
- `limit`

Ejemplo:

```bash
curl "http://localhost:8000/monitoreo?comuna=Talca&nivel_riesgo=critico&limit=10"
```

### Resumen y dataset

- `GET /resumen/comunas`
- `GET /dataset/ml`

## Cómo probar el POST /monitoreo

El campo `nivel_riesgo` no se envía desde la API porque PostgreSQL lo calcula automáticamente mediante trigger.

Ejemplo con `curl`:

```bash
curl -X POST "http://localhost:8000/monitoreo" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha_hora": "2026-06-17T10:00:00",
    "id_estacion": 1,
    "mp25": 42.5,
    "mp10": 75.1,
    "so2": 8.3,
    "no2": 19.7,
    "velocidad_viento": 4.8,
    "direccion_viento_grados": 180,
    "temperatura": 14.2,
    "humedad": 62.0,
    "fuente_dato": "api_fastapi"
  }'
```

Ejemplo en PowerShell:

```powershell
$body = @{
  fecha_hora = "2026-06-17T10:00:00"
  id_estacion = 1
  mp25 = 42.5
  mp10 = 75.1
  so2 = 8.3
  no2 = 19.7
  velocidad_viento = 4.8
  direccion_viento_grados = 180
  temperatura = 14.2
  humedad = 62.0
  fuente_dato = "api_fastapi"
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/monitoreo" -ContentType "application/json" -Body $body
```

## Cómo reiniciar la base de datos si cambia schema_seed.sql

PostgreSQL solo ejecuta `schema_seed.sql` la primera vez que crea el volumen. Si cambias el SQL y quieres reconstruir la base desde cero:

```bash
docker compose down -v
docker compose up --build
```

## Notas de implementación

- Se usa SQLAlchemy para la conexión y las consultas básicas.
- `GET /monitoreo`, `GET /resumen/comunas` y `GET /dataset/ml` consultan las vistas creadas por `schema_seed.sql`.
- El código está pensado para ser claro y simple, ideal para una evaluación.
