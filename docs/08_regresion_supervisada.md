# 08 - Regresion Supervisada MP2.5

## Objetivo

Se implementa un modelo supervisado para estimar el MP2.5 esperado en las proximas 24 horas usando el dataset consolidado por el proyecto en `data/processed/dataset_modelado.csv`.

## Preparacion de datos

- Se carga exclusivamente `dataset_modelado.csv`.
- Se corrigen etiquetas visibles con mojibake en `comuna` y `region`.
- Se ordena la serie por `codigo_estacion` y `fecha_hora`.
- La variable objetivo se construye como `mp25_24h_futuro` mediante `shift(-4)` por estacion, ya que la frecuencia es cada 6 horas.

## Ingenieria de variables

Variables base:

- `mp25`
- `mp10`
- `so2`
- `no2`
- `velocidad_viento`
- `direccion_viento_grados`
- `temperatura`
- `humedad`
- `emision_maxima_permitida`
- `indice_vulnerabilidad_respiratoria`
- `tipo_sensor`
- `comuna`
- `region`

Variables derivadas:

- `hora`
- `dia`
- `mes`
- `dia_semana`
- `lag_1`
- `lag_2`
- `rolling_mean_4`
- `direccion_viento_sin`
- `direccion_viento_cos`

`rolling_mean_4` se calcula usando solo valores pasados para evitar fuga temporal.

## Entrenamiento

Se comparan dos pipelines:

- `LinearRegression`
- `RandomForestRegressor`

Ambos usan un `ColumnTransformer` compartido:

- numericas: imputacion por mediana + `StandardScaler`
- categoricas: imputacion por moda + `OneHotEncoder`

El split es estrictamente temporal:

- 80% de filas mas antiguas para entrenamiento
- 20% de filas mas recientes para evaluacion
- sin `shuffle`

## Evaluacion

Las metricas reportadas para ambos modelos son:

- `MAE`
- `RMSE`
- `R2`

El mejor modelo se elige por menor `RMSE`.

## Artefactos generados

- `models/modelo_mp25_24h.joblib`
- `models/metricas_regresion.json`
- `data/processed/predicciones_mp25_24h.csv`

El CSV de predicciones mezcla:

- filas `evaluacion` para comparar real vs predicho
- filas `pronostico_24h` generadas a partir de la ultima observacion valida de cada estacion

## Integracion con el dashboard

El dashboard Streamlit consume:

- historico desde `dataset_modelado.csv`
- predicciones desde `predicciones_mp25_24h.csv`
- metricas desde `metricas_regresion.json`
- importancia de variables desde `modelo_mp25_24h.joblib`

La clasificacion ciudadana reutiliza la misma logica de MP2.5 de la API para no duplicar reglas.
