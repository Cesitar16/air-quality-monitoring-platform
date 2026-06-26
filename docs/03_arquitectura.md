# 03 - Arquitectura

## Objetivo

La plataforma busca centralizar datos de calidad del aire, exponerlos via API y reutilizarlos en analitica, modelamiento y visualizacion.

## Componentes

### 1. Fuentes de datos

Las entradas viven en `data/raw/`:

- `mediciones_oficiales.csv`
- `sensores_comunitarios.csv`
- `fiscalizacion_industrias.xlsx`
- `clima_historico.csv`
- `mapeo_estaciones.csv`

### 2. ETL

El modulo `etl/` ejecuta:

- extraccion
- transformacion
- validacion
- carga a la API
- export de `dataset_modelado.csv`

### 3. Base de datos y API

- PostgreSQL persiste comunas, estaciones, industrias y monitoreo.
- FastAPI expone endpoints REST y un endpoint analitico `/analytics/dataset-modelado`.

### 4. Ciencia de datos

La logica reusable vive en `src/`:

- `src/clustering.py`
- `src/regression.py`
- `src/preprocessing.py`
- `src/visualizations.py`

### 5. Dashboard

`dashboards/app.py` consume artefactos ya generados para presentar:

- vista ejecutiva
- vista tecnica
- vista ciudadana

## Flujo end-to-end

```text
data/raw
  -> etl/
  -> data/processed
  -> api + PostgreSQL
  -> /analytics/dataset-modelado
  -> src/clustering.py
  -> src/regression.py
  -> dashboards/app.py
```

## Artefactos

Persistencia analitica:

- `data/processed/dataset_modelado.csv`
- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `data/processed/predicciones_mp25_24h.csv`

Persistencia de modelos:

- `models/clustering/metricas_clustering.json`
- `models/clustering/kmeans_riesgo_ambiental.joblib`
- `models/clustering/scaler_clustering.joblib`
- `models/regression/metricas_regresion.json`
- `models/regression/modelo_mp25_24h.joblib`

## Decisiones de diseno

- `etl/` se mantiene separado de `src/` para no mezclar integracion con modelamiento.
- El entrenamiento debe funcionar con CSV local, sin depender del endpoint analitico.
- El dashboard no recalcula modelos; solo consume artefactos versionados o generados localmente.
- `docker-compose.yml` en la raiz sigue siendo el punto de entrada canonico para no romper el despliegue existente.
