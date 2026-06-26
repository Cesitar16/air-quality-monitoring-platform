# 06 - Modelamiento Clustering

## Objetivo

El clustering resume el dataset integrado en perfiles relativos de riesgo ambiental. La salida no reemplaza una categoria regulatoria oficial; sirve para segmentacion analitica y visualizacion.

## Dataset base

- `data/processed/dataset_modelado.csv`

## Variables usadas

El pipeline prioriza variables numericas disponibles como:

- `mp25`
- `mp10`
- `so2`
- `no2`
- `temperatura`
- `humedad`
- `velocidad_viento`
- `emision_maxima_permitida`
- `indice_vulnerabilidad_respiratoria`

## Pipeline

1. Carga del CSV local.
2. Conversion numerica e imputacion por mediana.
3. Eliminacion de columnas vacias o constantes.
4. Estandarizacion con `StandardScaler`.
5. Evaluacion de K entre 2 y 6.
6. Entrenamiento de `KMeans(n_clusters=3, random_state=42)`.
7. Asignacion de clusters y traduccion a etiquetas de riesgo.

## Artefactos

- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `models/clustering/kmeans_riesgo_ambiental.joblib`
- `models/clustering/scaler_clustering.joblib`
- `models/clustering/metricas_clustering.json`

## Ejecucion

```powershell
python src/clustering.py
```

O bien:

```powershell
.\scripts\run_clustering.ps1
```

## Validacion

`tests/test_clustering.py` cubre:

- preparacion de variables
- escalado
- entrenamiento K-Means
- asignacion de clusters
- generacion de etiquetas de riesgo
- export de artefactos

## Limitaciones

- el puntaje de riesgo es relativo al dataset disponible
- K=3 se selecciona por interpretabilidad y no por regulacion ambiental
- la estabilidad del clustering puede cambiar si el ETL incorpora nuevas comunas o sensores
