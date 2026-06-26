# 08 - Dashboard

## Objetivo

El dashboard Streamlit es la capa visual final del proyecto. Su proposito es traducir la salida del ETL y del modelamiento en una interfaz util para tres audiencias:

- autoridades o equipos municipales
- evaluadores tecnicos y analiticos
- ciudadanos o vecinos

## Aplicacion

- `dashboards/app.py`

## Fuentes de datos

El dashboard consume artefactos ya generados. No entrena modelos ni recalcula el ETL.

### Dataset base obligatorio

- `data/processed/dataset_modelado.csv`

### Artefactos opcionales

- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/metricas_regresion.json`
- `models/clustering/metricas_clustering.json`
- `models/regression/modelo_mp25_24h.joblib`

Si alguno de estos archivos opcionales no existe, la aplicacion muestra un mensaje claro en pantalla y degrada la vista afectada sin romper todo el dashboard.

## Dependencias

- `dashboards/requirements.txt`

Incluye al menos:

- `streamlit`
- `pandas`
- `plotly`
- `numpy`

## Estructura funcional

`dashboards/app.py` se organiza en funciones modulares como:

- `load_dataset()`
- `load_predictions()`
- `load_clusters()`
- `load_metrics()`
- `filter_data()`
- `render_sidebar()`
- `render_executive_view()`
- `render_technical_view()`
- `render_citizen_view()`
- `render_footer()`
- `main()`

## Layout general

La aplicacion usa:

- `st.set_page_config(layout="wide")`
- titulo general y descripcion breve
- sidebar con filtros globales
- selector de vista por audiencia
- graficos interactivos con Plotly
- tablas filtrables con `st.dataframe`

## Filtros implementados

El sidebar incorpora, cuando la columna existe:

- Region
- Comuna
- Tipo de sensor
- Rango de fechas
- Nivel de riesgo
- Categoria de alerta

Los filtros se aplican solo sobre los artefactos que tengan esas columnas, para evitar errores cuando falta algun archivo opcional.

## Vista Ejecutiva / Municipal

Objetivo:

- resumir el estado general del monitoreo
- identificar comunas criticas
- apoyar priorizacion preventiva

Indicadores y visualizaciones:

- MP2.5 promedio
- MP2.5 maximo
- total de mediciones
- comuna mas critica
- porcentaje de registros en alerta o riesgo
- prediccion promedio de MP2.5 a 24 horas
- ranking de comunas por MP2.5
- evolucion temporal de MP2.5
- resumen de alertas predictivas

## Vista Tecnica / Analitica

Objetivo:

- mostrar evidencia tecnica del comportamiento del modelo predictivo
- mostrar la segmentacion de riesgo generada por clustering

Indicadores y visualizaciones:

- MAE, RMSE y R2 del modelo ganador
- tabla comparativa de modelos
- scatter real vs predicho
- histograma de error absoluto
- importancia de variables cuando existe el modelo serializado
- metricas de clustering
- distribucion de clusters
- tabla resumen de perfiles de riesgo
- tabla filtrable de predicciones

## Vista Ciudadana / Vecinos

Objetivo:

- comunicar resultados en lenguaje simple
- ofrecer una lectura preventiva sin tecnicismos innecesarios

Elementos incluidos:

- selector de comuna
- estado actual de calidad del aire
- MP2.5 actual
- MP2.5 esperado para las proximas 24 horas
- mensaje simple de alerta temprana
- recomendacion general
- evolucion reciente de la comuna

## Categorias de alerta

Si el archivo de predicciones no trae categoria, el dashboard puede reconstruir `categoria_alerta_predicha` usando la misma clasificacion simple del proyecto:

- `Buena`: MP2.5 < 50
- `Regular`: 50 <= MP2.5 < 80
- `Alerta`: 80 <= MP2.5 < 110
- `Preemergencia`: 110 <= MP2.5 < 170
- `Emergencia`: MP2.5 >= 170

## Relacion con ETL, clustering y regresion

El dashboard depende del pipeline previo:

```text
ETL
    ->
dataset_modelado.csv
    ->
clustering + regresion
    ->
artefactos CSV / JSON / joblib
    ->
dashboard Streamlit
```

Esto permite una carga rapida y evita recalcular procesos pesados dentro de la interfaz.

## Manejo de errores

Se contemplan estos casos:

- falta `dataset_modelado.csv`: se detiene la app y se pide ejecutar ETL
- faltan predicciones: la vista ejecutiva y ciudadana avisan que no hay pronostico disponible
- faltan clusters o metricas: la vista tecnica muestra avisos parciales y sigue operativa
- falta el modelo guardado: no se muestra importancia de variables

## Limitaciones

- el dashboard depende de artefactos ya generados
- no corrige automaticamente datos faltantes
- no consulta internet ni fuentes externas
- la vista ciudadana simplifica el lenguaje y no entrega recomendaciones medicas especificas

## Ejecucion

Opcion recomendada:

```powershell
.\scripts\run_dashboard.ps1
```

Alternativa directa:

```powershell
streamlit run dashboards/app.py
```

## Evidencia visual

La carpeta `dashboards/screenshots/` queda disponible para almacenar capturas como:

- `vista_ejecutiva.png`
- `vista_tecnica.png`
- `vista_ciudadana.png`
