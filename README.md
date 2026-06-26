# Air Quality Monitoring Platform

## 1. Contexto del proyecto

Este repositorio implementa una plataforma academica de monitoreo de calidad del aire para comunas del centro-sur de Chile. El proyecto integra datos simulados de estaciones oficiales, sensores comunitarios, clima e industrias para construir una solucion completa de analitica ambiental.

La idea no es solo almacenar datos, sino recorrer todo el ciclo:

- extraer y limpiar fuentes heterogeneas
- publicar una API sobre PostgreSQL
- generar un dataset analitico reutilizable
- aplicar clustering para segmentar riesgo ambiental
- entrenar un modelo supervisado para pronosticar MP2.5 a 24 horas
- exponer resultados en un dashboard Streamlit

## 2. Objetivos funcionales

El proyecto hoy cubre cinco objetivos principales:

1. Consolidar un ETL reproducible y trazable.
2. Exponer los datos integrados por medio de una API REST con FastAPI.
3. Segmentar observaciones en perfiles de riesgo usando clustering.
4. Estimar la concentracion futura de MP2.5 para las proximas 24 horas.
5. Mostrar indicadores y pronosticos en una interfaz orientada a perfiles ejecutivos, tecnicos y ciudadanos.

## 3. Estado actual del repo

Actualmente el repositorio ya contiene una implementacion operativa de punta a punta:

- ETL documentado y con export completo de `dataset_modelado.csv`
- API FastAPI conectada a PostgreSQL
- pipeline de clustering en `src/clustering.py`
- pipeline de regresion en `src/regression.py`
- notebook narrativo de regresion en `notebooks/03_regresion_mp25_24h.ipynb`
- dashboard Streamlit en `dashboards/app.py`
- pruebas automatizadas sobre ETL, API, clustering y regresion
- artefactos versionados de metricas y salidas tabulares

## 4. Arquitectura general

El flujo principal del sistema es el siguiente:

```text
Fuentes raw CSV/XLSX
        ->
ETL local
        ->
PostgreSQL + API FastAPI
        ->
/analytics/dataset-modelado
        ->
data/processed/dataset_modelado.csv
        ->
Clustering + Regresion
        ->
Artefactos CSV / JSON / joblib
        ->
Dashboard Streamlit
```

### Componentes del stack

- Python para ETL, modelamiento y dashboard
- PostgreSQL 16 como base transaccional y analitica
- FastAPI + SQLAlchemy para la API REST
- scikit-learn para clustering y regresion
- Streamlit + Plotly para visualizacion
- Docker Compose para base de datos y API

## 5. Estructura del repositorio

```text
api/           API FastAPI, modelos y acceso a BD
dashboards/    app Streamlit y dependencias del dashboard
data/          datos raw, procesados y archivos exportados
db/            schema SQL y seeds de la base
docker/        Dockerfiles oficiales del proyecto
docs/          documentacion tecnica y operativa
etl/           extract, transform, validate, load y CLI del ETL
models/        artefactos persistidos de clustering y regresion
notebooks/     EDA, clustering y regresion narrativos
repo/          apoyo para evidencias Git y PRs
scripts/       atajos PowerShell para ejecucion local
src/           pipelines reutilizables de ciencia de datos
tests/         pruebas automatizadas
```

## 6. Fuentes de datos

Las entradas principales del caso estan en `data/raw/`:

- `mediciones_oficiales.csv`
- `sensores_comunitarios.csv`
- `fiscalizacion_industrias.xlsx`
- `clima_historico.csv`
- `mapeo_estaciones.csv`

Estas fuentes son simuladas con fines academicos. No representan mediciones oficiales en tiempo real.

## 7. Flujo del ETL

El ETL vive en `etl/` y sigue esta secuencia:

```text
extract -> transform -> validate -> load -> export dataset_modelado
```

### Responsabilidad de cada modulo

- `etl/extract.py`: lectura de fuentes y union inicial
- `etl/transform.py`: homologacion, limpieza y cruces
- `etl/validate.py`: reglas de calidad y registro de errores
- `etl/load.py`: carga a API, control de omitidas y export analitico
- `etl/run_pipeline.py`: punto de entrada CLI

### Salidas principales del ETL

- `data/processed/mediciones_limpias.csv`
- `data/processed/mediciones_validas.csv`
- `data/processed/industrias_limpias.csv`
- `data/processed/clima_limpio.csv`
- `data/processed/errores_etl.csv`
- `data/processed/payload_monitoreo_bulk.json`
- `data/processed/omitidas_carga_api.csv`
- `data/processed/reporte_carga_api.csv`
- `data/processed/dataset_modelado.csv`

### Mejora implementada en esta rama

`guardar_dataset_modelado()` ya no queda limitado a la primera pagina del endpoint analitico. Ahora recorre `/analytics/dataset-modelado` con `limit/offset` hasta agotar resultados, por lo que el CSV local queda completo para modelamiento y dashboard.

## 8. API y base de datos

La API esta en `api/app/` y corre sobre FastAPI. La base se levanta con PostgreSQL 16 usando:

- `db/schema.sql`
- `db/seed_calidad_aire_01_InviernoTemprano.sql`
- `db/seed_calidad_aire_02_inviernoIIntenso.sql`
- `db/seed_calidad_aire_03_primavera.sql`

### Endpoints relevantes para el pipeline

- `GET /health`
- `GET /estaciones`
- `GET /monitoreo`
- `POST /monitoreo/bulk`
- `GET /analytics/dataset-modelado`

## 9. Clustering implementado

El pipeline de clustering vive en `src/clustering.py` y opera sobre `data/processed/dataset_modelado.csv`.

### Variables principales del clustering

- `mp25`
- `mp10`
- `temperatura`
- `humedad`
- `velocidad_viento`
- `emision_maxima_permitida`
- `indice_vulnerabilidad_respiratoria`

### Algoritmo y estado actual

- algoritmo: `KMeans`
- `n_clusters = 3`
- filas procesadas: `26,622`
- silhouette actual: `0.2893`

### Artefactos generados

- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `models/clustering/kmeans_riesgo_ambiental.joblib`
- `models/clustering/scaler_clustering.joblib`
- `models/clustering/metricas_clustering.json`

## 10. Regresion supervisada implementada

La regresion fue construida para responder al requerimiento del caso:

> Estimar la concentracion de MP2.5 esperada para las proximas 24 horas.

### Dataset consumido

El modelo usa directamente:

- `data/processed/dataset_modelado.csv`

Eso significa que la regresion reutiliza la salida oficial del ETL y no trabaja sobre CSV raw aislados.

### Definicion del target

La serie tiene frecuencia de 6 horas, por lo que 24 horas equivalen a 4 pasos:

```text
24 horas / 6 horas = 4 pasos
```

Por eso el objetivo se construye como:

```text
mp25_24h = shift(-4)
```

### Features usadas en entrenamiento

Contaminacion actual:

- `mp25`
- `mp10`
- `so2`
- `no2`

Meteorologia:

- `velocidad_viento`
- `direccion_viento_grados`
- `temperatura`
- `humedad`

Contexto territorial:

- `emision_maxima_permitida`
- `indice_vulnerabilidad_respiratoria`
- `tipo_sensor`
- `comuna`
- `region`

Variables temporales:

- `hora`
- `dia`
- `mes`
- `dia_semana`
- `estacion_del_ano`

Ingenieria temporal:

- `lag_1`
- `lag_2`
- `lag_3`
- `delta_mp25`
- `mp25_promedio_movil_3`
- `rolling_mean_6`
- `rolling_mean_12`
- `direccion_viento_sin`
- `direccion_viento_cos`

### Modelos comparados

- `LinearRegression`
- `RandomForestRegressor`

Ambos se entrenan con un `ColumnTransformer` comun:

- numericas: imputacion + `StandardScaler`
- categoricas: imputacion + `OneHotEncoder(handle_unknown="ignore")`

### Esquema de validacion

- split temporal estricto: 80 por ciento mas antiguo para train y 20 por ciento mas reciente para test
- validacion adicional con `TimeSeriesSplit`
- seleccion del mejor modelo por menor `RMSE`

### Estado actual del modelo de regresion

Despues de reexportar el dataset completo desde la API y volver a entrenar:

- filas exportadas a `dataset_modelado.csv`: `26,622`
- filas utiles para supervision: `26,448`
- filas de entrenamiento: `21,158`
- filas de prueba: `5,290`
- mejor modelo: `random_forest`

Metricas actuales:

- `LinearRegression`: `MAE 3.2344`, `RMSE 4.6089`, `R2 0.6736`
- `RandomForestRegressor`: `MAE 2.1487`, `RMSE 3.9978`, `R2 0.7544`

### Artefactos guardados

Si, el modelo queda guardado. Los artefactos actuales son:

- `models/regression/modelo_mp25_24h.joblib`
- `models/regression/metricas_regresion.json`
- `data/processed/predicciones_mp25_24h.csv`

El archivo `predicciones_mp25_24h.csv` mezcla:

- filas de `evaluacion`
- filas de `pronostico_24h`

Esto permite alimentar el dashboard sin recalcular el modelo en tiempo real.

## 11. Dashboard

La aplicacion esta en:

- `dashboards/app.py`

### Entradas que consume

- `data/processed/dataset_modelado.csv`
- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/metricas_regresion.json`
- `models/regression/modelo_mp25_24h.joblib`

### Vistas implementadas

- `Vista Ejecutiva`: KPIs historicos, alertas y ranking de comunas
- `Vista Tecnica`: metricas, real vs predicho, importancia de variables y tabla filtrable
- `Vista Ciudadana`: estado por comuna, categoria y mensaje simple de alerta

El dashboard esta pensado para leer artefactos ya generados. No entrena modelos ni recalcula ETL al abrir.

## 12. Notebooks disponibles

- `notebooks/01_eda_calidad_aire.ipynb`
- `notebooks/02_clustering_riesgo_ambiental.ipynb`
- `notebooks/03_regresion_mp25_24h.ipynb`

El notebook de regresion importa funciones desde `src/regression.py`, por lo que la logica de entrenamiento no esta duplicada en celdas.

## 13. Requisitos del entorno

- Python 3.12 o 3.13 recomendado
- Docker Desktop para levantar PostgreSQL y la API
- PowerShell para los scripts versionados

Nota: con Python 3.14, `psycopg2-binary==2.9.10` puede requerir compilacion local adicional.

## 14. Instalacion

Instalacion completa del proyecto:

```powershell
python -m pip install -r requirements.txt
```

El `requirements.txt` raiz agrega:

- dependencias de `api/requirements.txt`
- `numpy`
- `matplotlib`
- `scikit-learn`
- `joblib`
- `streamlit`
- `plotly`
- `jupyter`
- `nbformat`

## 15. Convencion Docker vigente

La convencion actual es:

- unico compose oficial: `docker-compose.yml` en la raiz
- Dockerfiles oficiales: `docker/api.Dockerfile` y `docker/dashboard.Dockerfile`
- no se usa un compose secundario dentro de `docker/`

### Servicios disponibles

- `db`: PostgreSQL 16
- `api`: FastAPI
- `dashboard`: Streamlit opcional por profile

### Comandos Docker oficiales

Levantar base y API:

```powershell
docker compose up --build
```

Levantar tambien el dashboard:

```powershell
docker compose --profile dashboard up --build
```

Swagger:

- `http://localhost:8000/docs`

Dashboard opcional:

- `http://localhost:8501`

## 16. Ejecucion local paso a paso

### Opcion A: flujo completo recomendado

1. Instalar dependencias.
2. Levantar base y API con Docker.
3. Ejecutar ETL real para cargar y exportar el dataset integrado.
4. Ejecutar clustering.
5. Ejecutar regresion.
6. Levantar dashboard.

Comandos:

```powershell
python -m pip install -r requirements.txt
docker compose up --build -d
.\scripts\run_etl.ps1 --load-api
.\scripts\run_clustering.ps1
.\scripts\run_regression.ps1
.\scripts\run_dashboard.ps1
```

### Opcion B: comandos Python directos

```powershell
python etl/run_pipeline.py --load-api
python src/clustering.py
python src/regression.py
streamlit run dashboards/app.py
```

### Script para refrescar solo el dataset analitico

```powershell
python scripts/export_dataset_modelado.py
```

Esto vuelve a descargar `dataset_modelado.csv` desde la API paginando hasta completar todos los registros.

## 17. Scripts de ayuda

En `scripts/` existen estos atajos:

- `run_etl.ps1`
- `run_clustering.ps1`
- `run_regression.ps1`
- `run_dashboard.ps1`
- `run_tests.ps1`
- `export_dataset_modelado.py`

## 18. Pruebas automatizadas

La suite cubre API, ETL, clustering y regresion. En el estado actual se validaron:

- export completo de `dataset_modelado`
- construccion de target a 24 horas
- features temporales sin fuga
- entrenamiento y comparacion de ambos modelos
- serializacion del joblib
- generacion de predicciones y artefactos

Ejecucion:

```powershell
python -m pytest -q
```

## 19. Documentacion disponible

- `docs/03_arquitectura.md`
- `docs/05_etl_pipeline.md`
- `docs/06_modelamiento_clustering.md`
- `docs/07_modelamiento_regresion.md`
- `docs/08_dashboard.md`
- `docs/09_manual_usuario.md`
- `docs/10_despliegue_docker.md`

## 20. Limitaciones y supuestos actuales

- las fuentes son simuladas y no representan monitoreo oficial en vivo
- la regresion esta fijada a un horizonte de 24 horas
- la frecuencia de la serie usada por el modelo es de 6 horas
- el dashboard depende de artefactos previamente generados
- el clustering entrega perfiles relativos de riesgo y no categorias regulatorias oficiales

## 21. Resumen final

Hoy el proyecto ya dispone de una cadena completa y coherente:

- ETL reproducible
- API sobre PostgreSQL
- dataset integrado para analitica
- clustering operativo
- regresion supervisada con modelo guardado
- dashboard conectado a artefactos reales

El punto de entrada mas importante para entender el proyecto es este:

```text
ETL -> API -> dataset_modelado.csv -> clustering/regresion -> dashboard
```
