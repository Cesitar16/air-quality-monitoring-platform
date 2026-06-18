# Monitoreo de Calidad del Aire

## Contexto del proyecto

Este proyecto responde a la necesidad de una ONG ambiental y distintos municipios de la zona centro-sur de Chile de centralizar la información sobre calidad del aire. Actualmente los datos suelen estar dispersos, con formatos heterogéneos y tiempos de publicación que dificultan la detección temprana de episodios críticos de contaminación.

La iniciativa busca consolidar comunas, sensores, fuentes industriales y mediciones ambientales en una plataforma común. Esto permite preparar una base sólida para análisis posteriores, integración con dashboards, notebooks y futuros modelos predictivos.

## Objetivo del proyecto

En esta etapa, el foco es construir una base de datos reproducible en PostgreSQL y un backend REST con FastAPI que permita consultar e insertar información del sistema de monitoreo.

El alcance actual considera:

- levantar la base de datos con Docker
- cargar el esquema y las semillas del proyecto en el orden correcto
- exponer endpoints REST simples para las entidades principales
- dejar documentación Swagger lista para pruebas

## Estructura del repositorio

```text
.
├── api/
│   ├── app/
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   └── routes/
│   ├── Dockerfile
│   └── requirements.txt
├── db/
│   ├── schema.sql
│   ├── seed_calidad_aire_01_InviernoTemprano.sql
│   ├── seed_calidad_aire_02_inviernoIIntenso.sql
│   └── seed_calidad_aire_03_primavera.sql
├── docs/
│   ├── 01_contexto_negocio.md
│   └── 02_diccionario_datos.md
├── docker-compose.yml
├── .env.example
└── README.md
```

## Cómo ejecutar la BD

1. Crear el archivo `.env` desde el ejemplo:

```bash
cp .env.example .env
```

En PowerShell:

```powershell
Copy-Item .env.example .env
```

2. Levantar solo la base de datos:

```bash
docker compose up db
```

3. PostgreSQL ejecutará automáticamente, en este orden, durante la primera inicialización del volumen:

- `db/schema.sql`
- `db/seed_calidad_aire_01_InviernoTemprano.sql`
- `db/seed_calidad_aire_02_inviernoIIntenso.sql`
- `db/seed_calidad_aire_03_primavera.sql`

4. Si modificas el esquema o las semillas y quieres reconstruir la base desde cero:

```bash
docker compose down -v
docker compose up db
```

## Cómo ejecutar el backend

1. Levantar todo el proyecto:

```bash
docker compose up --build
```

2. Acceder a:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

3. Endpoints disponibles:

- `GET /`
- `GET /health`
- `GET /comunas`
- `GET /comunas/{id_comuna}`
- `GET /estaciones`
- `GET /estaciones/{id_estacion}`
- `GET /industrias`
- `GET /industrias/{id_industria}`
- `GET /monitoreo`
- `GET /monitoreo/{id_monitoreo}`
- `POST /monitoreo`

4. Filtros opcionales para `GET /monitoreo`:

- `comuna`
- `region`
- `fecha_inicio`
- `fecha_fin`
- `limit`

Ejemplo:

```bash
curl "http://localhost:8000/monitoreo?comuna=Talca&limit=10"
```

5. Ejemplo de `POST /monitoreo`:

```bash
curl -X POST "http://localhost:8000/monitoreo" \
  -H "Content-Type: application/json" \
  -d '{
    "fecha_hora": "2026-06-18T10:00:00",
    "id_estacion": 1,
    "mp25": 42.5,
    "mp10": 75.1,
    "so2": 8.3,
    "no2": 19.7,
    "velocidad_viento": 4.8,
    "direccion_viento_grados": 180,
    "temperatura": 14.2,
    "humedad": 62.0
  }'
```

En PowerShell:

```powershell
$body = @{
  fecha_hora = "2026-06-18T10:00:00"
  id_estacion = 1
  mp25 = 42.5
  mp10 = 75.1
  so2 = 8.3
  no2 = 19.7
  velocidad_viento = 4.8
  direccion_viento_grados = 180
  temperatura = 14.2
  humedad = 62.0
} | ConvertTo-Json

Invoke-RestMethod -Method Post -Uri "http://localhost:8000/monitoreo" -ContentType "application/json" -Body $body
```
