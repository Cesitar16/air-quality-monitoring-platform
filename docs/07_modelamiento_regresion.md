# 07 - Modelamiento Regresion

## Objetivo

Entrenar un modelo supervisado que estime la concentracion de MP2.5 esperada en las proximas 24 horas usando contaminantes actuales, variables meteorologicas, contexto territorial e historial reciente por estacion.

## Dataset base

- `data/processed/dataset_modelado.csv`

## Objetivo supervisado

Se construye `mp25_24h` por estacion con `shift(-4)` porque la serie esta muestreada cada 6 horas:

```text
24 horas / 6 horas = 4 pasos
```

Tambien se conserva la columna legacy `mp25_24h_futuro` para compatibilidad.

## Features

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
- `mp25_promedio_movil_3`
- `rolling_mean_4`
- `direccion_viento_sin`
- `direccion_viento_cos`

## Modelos comparados

- `LinearRegression`
- `RandomForestRegressor`

## Preprocesamiento

- numericas: imputacion por mediana + `StandardScaler`
- categoricas: imputacion por moda + `OneHotEncoder(handle_unknown="ignore")`

## Evaluacion

- split temporal 80/20
- metricas `MAE`, `RMSE`, `R2`
- seleccion del mejor modelo por menor `RMSE`

## Artefactos

- `models/regression/modelo_mp25_24h.joblib`
- `models/regression/metricas_regresion.json`
- `data/processed/predicciones_mp25_24h.csv`

El CSV exporta tanto columnas de compatibilidad con la pauta como columnas mas explicitas para dashboard:

- `fecha_hora`
- `codigo_estacion`
- `comuna`
- `region`
- `mp25_real_24h`
- `mp25_predicho_24h`
- `error_absoluto`
- `categoria_alerta_predicha`
- `tipo_registro`
- `fecha_hora_base`
- `fecha_hora_objetivo`

## Ejecucion

```powershell
python src/regression.py
```

O bien:

```powershell
.\scripts\run_regression.ps1
```

## Validacion

`tests/test_regression.py` valida:

- columnas requeridas
- construccion del target a 24h
- features sin fuga temporal
- entrenamiento de ambos modelos
- seleccion del mejor por RMSE
- serializacion y carga del pipeline
- generacion del CSV de predicciones

## Limitaciones

- el horizonte es fijo y depende de la frecuencia actual del dataset
- no hay validacion cross-time-series por comuna aparte del split temporal global
- el pronostico usa la ultima observacion valida disponible por estacion
