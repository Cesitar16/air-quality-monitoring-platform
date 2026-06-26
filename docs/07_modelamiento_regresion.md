# 07 - Modelamiento Regresion

## 1. Objetivo del modelo

El caso de negocio pide estimar la concentracion esperada de MP2.5 para las proximas 24 horas.

Por eso la variable objetivo del modelo es:

- `mp25_24h`

Es decir:

- el valor futuro de `mp25`
- 24 horas despues
- para la misma serie temporal

No se modela:

- `categoria_ica`
- `cluster`
- `nivel_riesgo`

Esas variables pertenecen a capas de interpretacion o al modelamiento no supervisado, no al objetivo de regresion.

## 2. Fuente de datos usada

El modelo consume directamente:

- `data/processed/dataset_modelado.csv`

La decision fue deliberada porque este dataset ya pasa por:

- ETL
- limpieza y validaciones
- integracion con clima
- integracion territorial
- export desde la API analitica

Eso permite defender que la regresion reutiliza la salida oficial del pipeline de datos del proyecto y no trabaja sobre archivos raw aislados.

## 3. Que se implemento sobre el modelo

Durante esta iteracion se consolidaron las siguientes decisiones:

1. Se dejo `src/regression.py` como pipeline ejecutable completo.
2. Se fijo el objetivo a 24 horas con frecuencia de 6 horas.
3. Se usaron features de contaminacion, meteorologia, contexto territorial e historial temporal.
4. Se evito fuga temporal en lags y promedios moviles.
5. Se compararon dos modelos:
   - `LinearRegression`
   - `RandomForestRegressor`
6. Se uso split temporal 80/20 en vez de mezcla aleatoria.
7. Se agrego validacion adicional con `TimeSeriesSplit`.
8. Se guardan artefactos para dashboard y analisis posterior.
9. Se regenero `dataset_modelado.csv` desde la API para usar la version grande de la base y no la version chica de `dry-run`.

## 4. Dataset final usado en la version actual

Despues de volver a exportar el dataset desde `/analytics/dataset-modelado`, el modelo quedo entrenando con:

- `26.622` filas en `dataset_modelado.csv`
- `44` estaciones
- `27` comunas
- `16` columnas de entrada provenientes del dataset integrado

Luego de construir el objetivo a 24 horas y remover filas sin target:

- `26.448` filas utilizables para entrenamiento supervisado
- `21.158` filas de entrenamiento
- `5.290` filas de prueba

Esto reemplazo una version previa mucho mas pequena del CSV, que venia de `dry-run` y solo dejaba 60 filas.

## 5. Construccion de la variable objetivo

La serie base tiene frecuencia de 6 horas, por lo que 24 horas equivalen a 4 pasos:

```text
24 horas / 6 horas = 4 pasos
```

Por eso el target se construye como:

```text
mp25_24h = shift(-4)
```

Implementacion actual:

- primero se intenta construir el target por `codigo_estacion`
- si una estacion no tiene suficiente historia, existe un fallback por `comuna`

Ademas se conserva:

- `mp25_24h_futuro`

como columna legacy para compatibilidad con pruebas y artefactos anteriores.

## 6. Preprocesamiento del dataset

Antes de entrenar, el pipeline hace:

### 6.1 Normalizacion de texto

- correccion de mojibake en `comuna`, `region`, `tipo_sensor`, `codigo_estacion`

### 6.2 Compatibilidad con datasets pequenos

Si el CSV proviene de `dry-run` y faltan columnas de contexto:

- se infiere `tipo_sensor`
- se completa `indice_vulnerabilidad_respiratoria`
- se completa `emision_maxima_permitida`

Esto permite que el script siga siendo ejecutable incluso con una version reducida del dataset, aunque el entrenamiento serio se realiza con la version grande exportada desde la API.

### 6.3 Orden temporal

Las filas se ordenan por:

- `codigo_estacion`
- `fecha_hora`

para construir correctamente la memoria temporal.

## 7. Variables usadas por el modelo

El pipeline final considera cuatro grupos de variables.

### 7.1 Contaminacion actual

- `mp25`
- `mp10`
- `so2`
- `no2`

### 7.2 Meteorologia

- `velocidad_viento`
- `direccion_viento_grados`
- `temperatura`
- `humedad`

### 7.3 Contexto territorial

- `emision_maxima_permitida`
- `indice_vulnerabilidad_respiratoria`
- `tipo_sensor`
- `comuna`
- `region`

### 7.4 Variables temporales

- `hora`
- `dia`
- `mes`
- `dia_semana`
- `estacion_del_ano`

`estacion_del_ano` se deriva del mes usando estacionalidad del hemisferio sur:

- verano
- otono
- invierno
- primavera

## 8. Ingenieria de caracteristicas

Para capturar la memoria del sistema se agregaron variables historicas:

- `lag_1`
- `lag_2`
- `lag_3`

Estas representan el MP2.5 observado en pasos anteriores de la serie.

Tambien se construyeron:

- `delta_mp25`
- `mp25_promedio_movil_3`
- `rolling_mean_6`
- `rolling_mean_12`

Interpretacion:

- `delta_mp25` ayuda a detectar si la contaminacion viene subiendo o bajando
- los promedios moviles suavizan fluctuaciones y capturan tendencia reciente

Finalmente, la direccion del viento se representa con variables circulares:

- `direccion_viento_sin`
- `direccion_viento_cos`

Esto evita tratar 0 y 360 grados como valores artificialmente lejanos.

## 9. Preprocesamiento dentro del pipeline de sklearn

Se usa un `ColumnTransformer` comun a ambos modelos.

### Variables numericas

- imputacion por mediana
- `StandardScaler`

### Variables categoricas

- imputacion por valor mas frecuente
- `OneHotEncoder(handle_unknown="ignore")`

Esto permite usar el mismo stack para comparar modelos de forma justa.

## 10. Modelos comparados

Se entrenan dos candidatos:

### 10.1 Linear Regression

Se uso como linea base interpretable y para justificar comparacion con un modelo simple.

### 10.2 Random Forest Regressor

Se uso como modelo principal porque puede capturar relaciones no lineales entre:

- contaminantes
- meteorologia
- contexto territorial
- memoria temporal

El criterio de seleccion del mejor modelo es:

- menor `RMSE`

## 11. Esquema de entrenamiento y validacion

### 11.1 Split principal

Se aplica una particion estrictamente temporal:

- 80% mas antiguo para train
- 20% mas reciente para test

No se usa `shuffle=True` porque eso rompería la logica temporal del problema.

### 11.2 Validacion adicional

Sobre el conjunto de entrenamiento se agrego:

- `TimeSeriesSplit`

Esto no reemplaza el holdout final, pero entrega una señal extra de estabilidad temporal.

## 12. Resultados actuales del modelo

Con el dataset grande exportado desde la API, el mejor modelo actual es:

- `random_forest`

Metricas en el conjunto de prueba:

### Linear Regression

- `MAE = 3.2344`
- `RMSE = 4.6089`
- `R2 = 0.6736`

### Random Forest Regressor

- `MAE = 2.1487`
- `RMSE = 3.9978`
- `R2 = 0.7544`

Interpretacion:

- el `RandomForestRegressor` fue mejor en las tres metricas
- el error medio absoluto baja a aproximadamente 2.15 unidades de MP2.5
- el modelo explica cerca de un 75.4% de la variabilidad observada en test

En esta version, el modelo ya no queda limitado por un conjunto de prueba de 6 filas. El holdout actual tiene 5.290 filas, por lo que la evaluacion es mucho mas confiable.

## 13. Importancia de variables

Segun el modelo actual, las variables con mayor peso quedaron aproximadamente asi:

1. `mp25`
2. `dia_semana`
3. `dia`
4. `mp10`
5. `temperatura`
6. `mes`
7. `humedad`
8. `velocidad_viento`
9. `rolling_mean_12`
10. `so2`

Lectura general:

- `mp25` actual domina claramente la prediccion
- las variables temporales (`dia_semana`, `dia`, `mes`) ganaron relevancia al ampliar el dataset
- la meteorologia sigue aportando senal
- la memoria temporal tambien participa, aunque con menor peso que el valor actual

## 14. Artefactos generados

El pipeline guarda:

- `models/regression/modelo_mp25_24h.joblib`
- `models/regression/metricas_regresion.json`
- `data/processed/predicciones_mp25_24h.csv`

### Contenido del JSON de metricas

Incluye:

- horizonte
- frecuencia
- `target_shift_steps`
- filas de train/test
- mejor modelo
- features usadas
- metricas por modelo
- resultados de `TimeSeriesSplit`

### Contenido del CSV de predicciones

El archivo mezcla dos tipos de registros:

- `evaluacion`
- `pronostico_24h`

Columnas relevantes:

- `fecha_hora`
- `fecha_hora_base`
- `fecha_hora_objetivo`
- `codigo_estacion`
- `comuna`
- `region`
- `mp25_actual`
- `mp25_real_24h`
- `mp25_predicho_24h`
- `error_absoluto`
- `categoria_alerta_predicha`

## 15. Clasificacion ciudadana

Despues de predecir el MP2.5 futuro, el pipeline traduce ese valor a una categoria de alerta reutilizando la misma logica de la API:

- Buena
- Regular
- Alerta
- Preemergencia
- Emergencia

Esto permite que el dashboard muestre resultados entendibles para usuarios no tecnicos sin recalcular reglas aparte.

## 16. Integracion con el dashboard

El dashboard no entrena ni recalcula modelos.

Solo consume:

- `dataset_modelado.csv`
- `predicciones_mp25_24h.csv`
- `metricas_regresion.json`
- `modelo_mp25_24h.joblib`

Eso hace que la carga visual sea rapida y que la capa de modelamiento quede desacoplada de la interfaz.

## 17. Pruebas automatizadas

`tests/test_regression.py` cubre:

- validacion de columnas requeridas
- correccion de mojibake
- soporte para CSV reducido de `dry-run`
- construccion correcta del target a 24h
- lags y medias moviles sin fuga temporal
- fallback por comuna cuando una estacion no alcanza
- entrenamiento de ambos modelos
- seleccion del mejor por `RMSE`
- serializacion y carga del pipeline
- generacion del CSV de predicciones

## 18. Flujo completo actual

```text
Fuentes raw CSV/XLSX
        ->
ETL
        ->
API + PostgreSQL
        ->
/analytics/dataset-modelado
        ->
data/processed/dataset_modelado.csv
        ->
Preprocesamiento
        ->
Ingenieria de caracteristicas
        ->
Split temporal
        ->
Linear Regression
        ->
Random Forest
        ->
Comparacion de metricas
        ->
Guardar mejor modelo
        ->
predicciones_mp25_24h.csv
        ->
Dashboard Streamlit
```

## 19. Limitaciones actuales

- El horizonte sigue siendo fijo a 24 horas.
- El modelo depende de la frecuencia de 6 horas del dataset actual.
- `TimeSeriesSplit` entrega una senal adicional, pero algunos folds pueden variar bastante segun el periodo temporal.
- Aun se podria probar una validacion por estacion o por comuna para evaluar generalizacion mas fina.
- No se implemento aun un tercer modelo como `GradientBoostingRegressor` o `XGBoost`.

## 20. Conclusion

La regresion quedo alineada con el caso de negocio:

- usa la salida oficial del ETL
- predice `MP2.5 +24h`
- incorpora contaminacion, clima, contexto y memoria temporal
- evita fuga temporal
- compara una linea base con un modelo no lineal
- guarda artefactos reutilizables para el dashboard

Con el dataset grande exportado desde la API, el `RandomForestRegressor` alcanzo el mejor desempeno y se consolidó como el modelo final actual del proyecto.
