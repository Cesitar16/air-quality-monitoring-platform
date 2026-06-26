# Dashboard Streamlit

## Que muestra

El dashboard es la capa visual final del proyecto de monitoreo de calidad del aire. Resume:

- estado historico de MP2.5
- comunas criticas
- resultados de clustering de riesgo ambiental
- predicciones de MP2.5 para las proximas 24 horas
- mensajes diferenciados para audiencias ejecutivas, tecnicas y ciudadanas

## Archivos que necesita

El dashboard intenta leer estos artefactos si existen:

- `data/processed/dataset_modelado.csv`
- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/metricas_regresion.json`
- `models/clustering/metricas_clustering.json`
- `models/regression/modelo_mp25_24h.joblib` para importancia de variables

## Comportamiento si faltan archivos

- Si falta `dataset_modelado.csv`, la aplicacion se detiene y pide ejecutar primero el ETL.
- Si faltan predicciones, clustering o metricas, la aplicacion sigue funcionando y muestra avisos claros en las vistas afectadas.
- Si falta el modelo serializado, simplemente no se muestra la importancia de variables.

## Vistas implementadas

- `Vista Ejecutiva / Municipal`
  - KPIs historicos
  - ranking de comunas
  - evolucion temporal de MP2.5
  - resumen de alertas predictivas

- `Vista Tecnica / Analitica`
  - metricas de regresion
  - real vs predicho
  - histograma de errores
  - importancia de variables
  - distribucion y resumen de clusters

- `Vista Ciudadana / Vecinos`
  - selector de comuna
  - estado actual
  - pronostico a 24 horas
  - mensaje simple de alerta
  - evolucion reciente

## Como ejecutarlo

Opcion recomendada:

```powershell
.\scripts\run_dashboard.ps1
```

Alternativa directa:

```powershell
streamlit run dashboards/app.py
```

## Dependencias

```powershell
python -m pip install -r dashboards/requirements.txt
```

## Notas operativas

- El dashboard no entrena modelos.
- El dashboard no ejecuta ETL.
- Todos los calculos pesados deben haberse generado antes en los artefactos del proyecto.
