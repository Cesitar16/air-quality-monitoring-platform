# 05 - ETL Pipeline

## Objetivo

El ETL integra fuentes simuladas de calidad del aire, normaliza los datos, aplica validaciones ambientales y prepara la carga hacia la API. El mismo flujo deja disponible `data/processed/dataset_modelado.csv` para notebooks, clustering, regresion y dashboard.

## Entradas

- `data/raw/mediciones_oficiales.csv`
- `data/raw/sensores_comunitarios.csv`
- `data/raw/fiscalizacion_industrias.xlsx`
- `data/raw/clima_historico.csv`
- `data/raw/mapeo_estaciones.csv`

## Flujo

```text
extract -> transform -> validate -> load -> export dataset_modelado
```

## Modulos

- `etl/extract.py`: lectura de fuentes y unificacion inicial
- `etl/transform.py`: limpieza, homologacion y cruces
- `etl/validate.py`: reglas de calidad y trazabilidad de errores
- `etl/load.py`: carga a API, omitidas, reportes y dataset analitico
- `etl/run_pipeline.py`: punto de entrada CLI

## Salidas

- `data/processed/mediciones_limpias.csv`
- `data/processed/mediciones_validas.csv`
- `data/processed/industrias_limpias.csv`
- `data/processed/clima_limpio.csv`
- `data/processed/errores_etl.csv`
- `data/processed/payload_monitoreo_bulk.json`
- `data/processed/omitidas_carga_api.csv`
- `data/processed/reporte_carga_api.csv`
- `data/processed/dataset_modelado.csv`

## Integracion con la API

El ETL usa:

- `GET /health`
- `GET /estaciones`
- `GET /monitoreo`
- `POST /monitoreo/bulk`
- `GET /analytics/dataset-modelado`

## Reglas operativas relevantes

- El mapeo de estaciones privilegia match exacto y luego mapeo manual seguro.
- Las mediciones ya presentes en API se registran como omitidas, no se reenvian.
- El clima incompleto puede pasar la validacion ambiental, pero no la carga real al endpoint bulk.
- `--load-api` falla de forma explicita si la API no esta disponible.

## Export de dataset_modelado

`guardar_dataset_modelado()` recorre `/analytics/dataset-modelado` con `limit/offset` hasta agotar resultados. Eso evita el corte historico de 100 filas y garantiza que el CSV local quede completo para modelamiento.

## Ejecucion

Dry-run:

```powershell
python etl/run_pipeline.py --dry-run
```

Carga real:

```powershell
python etl/run_pipeline.py --load-api
```

Script de ayuda:

```powershell
.\scripts\run_etl.ps1 --load-api
```

## Validaciones

- esquema minimo obligatorio
- contaminantes no negativos
- humedad valida cuando existe
- direccion del viento en rango
- deduplicacion por estacion y fecha
- trazabilidad completa en `errores_etl.csv`

## Limitaciones

- las fuentes son simuladas
- la calidad del mapeo depende de `mapeo_estaciones.csv`
- si la API esta semillada previamente, puede haber `0 insertados` por duplicados ya existentes
