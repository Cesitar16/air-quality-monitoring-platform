# Air Quality Monitoring Platform

## Resumen

Este repositorio concentra un caso academico de monitoreo de calidad del aire para comunas del centro-sur de Chile. La solucion integra:

- ETL reproducible sobre fuentes simuladas
- API REST con FastAPI y PostgreSQL
- modelamiento no supervisado para riesgo ambiental
- regresion supervisada para pronostico de MP2.5 a 24 horas
- dashboard Streamlit para perfiles ejecutivos, tecnicos y ciudadanos

## Arquitectura

El flujo principal del proyecto es:

```text
Fuentes raw CSV/XLSX
        ->
ETL local
        ->
PostgreSQL + API
        ->
dataset_modelado.csv
        ->
clustering + regresion
        ->
artefactos CSV/JSON/joblib
        ->
dashboard Streamlit
```

Mas detalle en [docs/03_arquitectura.md](/E:/ProjectsGithub/air-quality-monitoring-platform/docs/03_arquitectura.md).

## Estructura del repositorio

```text
api/           API FastAPI y acceso a BD
dashboards/    app Streamlit, dependencias y README
data/          datos raw, procesados y README operativo
db/            schema y seeds de PostgreSQL
docker/        referencia de despliegue y Dockerfiles auxiliares
docs/          documentacion formal del proyecto
etl/           extraccion, transformacion, validacion y carga
models/        artefactos de clustering y regresion
notebooks/     EDA, clustering y regresion
repo/          plantillas para evidencias Git
scripts/       atajos PowerShell
src/           logica reutilizable de ciencia de datos
tests/         pruebas automatizadas y reporte
```

## Requisitos

- Python 3.12 o 3.13 recomendado
- Docker Desktop para levantar PostgreSQL y la API
- PowerShell para ejecutar los scripts versionados

Nota: en Python 3.14 `psycopg2-binary==2.9.10` puede requerir compilacion local. Para desarrollo rapido se recomienda Python 3.12/3.13 o usar Docker para la API.

## Instalacion

Instalacion general del proyecto:

```powershell
python -m pip install -r requirements.txt
```

Dependencias solo para dashboard:

```powershell
python -m pip install -r dashboards/requirements.txt
```

## Ejecucion rapida

Levantar servicios base:

```powershell
docker compose up --build
```

Ejecutar ETL:

```powershell
.\scripts\run_etl.ps1 --load-api
```

Ejecutar clustering:

```powershell
.\scripts\run_clustering.ps1
```

Ejecutar regresion:

```powershell
.\scripts\run_regression.ps1
```

Levantar dashboard:

```powershell
.\scripts\run_dashboard.ps1
```

Ejecutar pruebas:

```powershell
.\scripts\run_tests.ps1
```

## Artefactos principales

ETL:

- `data/processed/mediciones_limpias.csv`
- `data/processed/mediciones_validas.csv`
- `data/processed/industrias_limpias.csv`
- `data/processed/clima_limpio.csv`
- `data/processed/errores_etl.csv`
- `data/processed/dataset_modelado.csv`

Clustering:

- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `models/clustering/kmeans_riesgo_ambiental.joblib`
- `models/clustering/scaler_clustering.joblib`
- `models/clustering/metricas_clustering.json`

Regresion:

- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/modelo_mp25_24h.joblib`
- `models/regression/metricas_regresion.json`

## Documentacion

- [docs/05_etl_pipeline.md](/E:/ProjectsGithub/air-quality-monitoring-platform/docs/05_etl_pipeline.md)
- [docs/06_modelamiento_clustering.md](/E:/ProjectsGithub/air-quality-monitoring-platform/docs/06_modelamiento_clustering.md)
- [docs/07_modelamiento_regresion.md](/E:/ProjectsGithub/air-quality-monitoring-platform/docs/07_modelamiento_regresion.md)
- [docs/08_dashboard.md](/E:/ProjectsGithub/air-quality-monitoring-platform/docs/08_dashboard.md)
- [docs/09_manual_usuario.md](/E:/ProjectsGithub/air-quality-monitoring-platform/docs/09_manual_usuario.md)

## Validacion sugerida

```powershell
python -m pytest -q
python etl/run_pipeline.py --dry-run
python src/clustering.py
python src/regression.py
streamlit run dashboards/app.py
```

## Limitaciones

- Las fuentes son simuladas y no representan mediciones oficiales actuales.
- El clustering entrega perfiles relativos de riesgo, no categorias regulatorias.
- La regresion usa un horizonte fijo de 24 horas con frecuencia de 6 horas.
- El dashboard depende de artefactos previamente generados por ETL y modelamiento.
