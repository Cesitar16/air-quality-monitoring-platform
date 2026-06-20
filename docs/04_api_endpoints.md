# 04 - API Endpoints

## Descripción general de la API

Esta API expone información del proyecto de monitoreo de calidad del aire para la zona centro-sur de Chile. Su objetivo es actuar como capa de servicios entre PostgreSQL y consumidores como dashboards, ETL y notebooks.

La API está construida con FastAPI, SQLAlchemy y PostgreSQL.

## Cómo levantar la API

Desde la raíz del proyecto:

```bash
docker compose up --build
```

## URL de Swagger

```text
http://localhost:8000/docs
```

## Tabla de endpoints

| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Verifica que la API y PostgreSQL estén operativos |
| GET | `/comunas` | Lista comunas |
| GET | `/comunas/{id_comuna}` | Obtiene una comuna por id |
| GET | `/estaciones` | Lista estaciones y sensores |
| GET | `/estaciones/{id_estacion}` | Obtiene una estación por id |
| GET | `/industrias` | Lista industrias |
| GET | `/industrias/{id_industria}` | Obtiene una industria por id |
| GET | `/monitoreo` | Lista mediciones con filtros y paginación |
| GET | `/monitoreo/{id_monitoreo}` | Obtiene una medición por id |
| POST | `/monitoreo` | Inserta una medición individual |
| POST | `/monitoreo/bulk` | Inserta mediciones en forma masiva |
| GET | `/analytics/resumen-general` | Resumen general del sistema |
| GET | `/analytics/mp25-por-comuna` | Promedio de MP2.5 por comuna |
| GET | `/analytics/comunas-criticas` | Ranking de comunas más críticas |
| GET | `/analytics/evolucion-mp25` | Serie temporal de MP2.5 |
| GET | `/analytics/ica-por-comuna` | Categoría ciudadana por comuna |
| GET | `/analytics/ranking-sensores` | Ranking de sensores por contaminación promedio |
| GET | `/analytics/dataset-modelado` | Dataset unido para EDA y modelado |

## Parámetros aceptados

### GET /health

Sin parámetros.

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "air-quality-api",
  "database": "connected"
}
```

### GET /comunas

Sin parámetros.

### GET /comunas/{id_comuna}

Parámetro de ruta:

- `id_comuna`

### GET /estaciones

Sin parámetros.

### GET /estaciones/{id_estacion}

Parámetro de ruta:

- `id_estacion`

### GET /industrias

Sin parámetros.

### GET /industrias/{id_industria}

Parámetro de ruta:

- `id_industria`

### GET /monitoreo

Parámetros de query disponibles:

- `comuna`
- `id_estacion`
- `id_comuna`
- `region`
- `fecha_inicio`
- `fecha_fin`
- `mp25_min`
- `mp25_max`
- `tipo_sensor`
- `limit`
- `offset`

Ejemplo:

```bash
curl "http://localhost:8000/monitoreo?region=Maule&fecha_inicio=2026-06-01&fecha_fin=2026-06-30&mp25_min=50&limit=50&offset=0"
```

### GET /monitoreo/{id_monitoreo}

Parámetro de ruta:

- `id_monitoreo`

### POST /monitoreo

Request:

```json
{
  "fecha_hora": "2026-06-20T08:00:00",
  "id_estacion": 1,
  "mp25": 55.2,
  "mp10": 90.4,
  "so2": 10.5,
  "no2": 15.1,
  "velocidad_viento": 2.7,
  "direccion_viento_grados": 180,
  "temperatura": 10.2,
  "humedad": 62.0
}
```

### POST /monitoreo/bulk

Comportamiento:

- valida cada registro individualmente
- inserta los válidos
- reporta errores parciales sin detener toda la carga

Request:

```json
{
  "mediciones": [
    {
      "fecha_hora": "2026-06-20T08:00:00",
      "id_estacion": 1,
      "mp25": 55.2,
      "mp10": 90.4,
      "so2": 10.5,
      "no2": 15.1,
      "velocidad_viento": 2.7,
      "direccion_viento_grados": 180,
      "temperatura": 10.2,
      "humedad": 62.0
    }
  ]
}
```

Response:

```json
{
  "insertados": 1,
  "errores": 0,
  "detalle_errores": []
}
```

### GET /analytics/resumen-general

Sin parámetros.

### GET /analytics/mp25-por-comuna

Parámetros opcionales:

- `region`
- `fecha_inicio`
- `fecha_fin`

### GET /analytics/comunas-criticas

Parámetros opcionales:

- `limit`

### GET /analytics/evolucion-mp25

Parámetros opcionales:

- `id_comuna`
- `region`
- `fecha_inicio`
- `fecha_fin`

### GET /analytics/ica-por-comuna

Parámetros opcionales:

- `region`
- `fecha_inicio`
- `fecha_fin`

Clasificación simplificada usada para MP2.5:

- `Buena`: menor a 50
- `Regular`: 50 a 79.99
- `Alerta`: 80 a 109.99
- `Preemergencia`: 110 a 169.99
- `Emergencia`: 170 o más

### GET /analytics/ranking-sensores

Parámetros opcionales:

- `limit`

### GET /analytics/dataset-modelado

Parámetros opcionales:

- `region`
- `id_comuna`
- `fecha_inicio`
- `fecha_fin`
- `limit`
- `offset`

## Ejemplos de response

### GET /analytics/resumen-general

```json
{
  "total_comunas": 27,
  "total_estaciones": 44,
  "total_industrias": 30,
  "total_mediciones": 26672,
  "mp25_promedio": 58.4,
  "mp25_maximo": 175.0,
  "comuna_mas_critica": "Chillan"
}
```

### GET /analytics/ica-por-comuna

```json
[
  {
    "comuna": "Talca",
    "region": "Maule",
    "mp25_promedio": 74.3,
    "categoria": "Regular",
    "mensaje_ciudadano": "Personas sensibles deberian reducir exposicion prolongada.",
    "color_referencial": "amarillo"
  }
]
```

## Errores comunes

### 404

```json
{
  "detail": "No existe una comuna con id_comuna=999"
}
```

### 422

```json
{
  "detail": "Error de validacion en la solicitud.",
  "errores": []
}
```

### 500

```json
{
  "detail": "Error interno controlado en la API."
}
```
