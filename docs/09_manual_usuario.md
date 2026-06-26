# 09 - Manual de Usuario

## Requisitos

- Python 3.12 o 3.13 recomendado para instalar dependencias locales del proyecto
- Docker Desktop si se quiere levantar PostgreSQL y FastAPI con la configuracion versionada

## Instalacion

Desde la raiz del repositorio:

```bash
python -m pip install -r requirements.txt
```

Si tambien se quiere ejecutar la API localmente fuera de Docker:

```bash
python -m pip install -r api/requirements.txt
```

## Ejecutar ETL

Modo local sin envio a API:

```bash
python etl/run_pipeline.py --dry-run
```

Modo con API levantada:

```bash
docker compose up --build
python etl/run_pipeline.py --load-api
```

El ETL deja sus salidas en `data/processed/`, incluyendo `dataset_modelado.csv`.

## Ejecutar regresion

Entrenamiento y exportacion de artefactos:

```bash
python src/regression.py
```

Artefactos generados:

- `models/modelo_mp25_24h.joblib`
- `models/metricas_regresion.json`
- `data/processed/predicciones_mp25_24h.csv`

## Ejecutar dashboard

Con los artefactos ya generados:

```bash
streamlit run dashboards/app.py
```

El dashboard usa:

- `data/processed/dataset_modelado.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/metricas_regresion.json`
- `models/modelo_mp25_24h.joblib`

## Ejecutar pruebas

Pruebas ETL y API:

```bash
pytest tests/test_etl_load.py
pytest tests/test_api_analytics.py
```

Pruebas de regresion:

```bash
pytest tests/test_regression.py
```
