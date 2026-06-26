# 08 - Dashboard

## Objetivo

El dashboard Streamlit resume historico, clusters y pronosticos de MP2.5 en una interfaz unica para distintos perfiles de usuario.

## Aplicacion

- `dashboards/app.py`

## Dependencias

- `dashboards/requirements.txt`

## Entradas consumidas

- `data/processed/dataset_modelado.csv`
- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/metricas_regresion.json`
- `models/regression/modelo_mp25_24h.joblib` para importancia de variables cuando exista

## Vistas

### Vista Ejecutiva

- MP2.5 promedio historico
- MP2.5 maximo
- comuna critica
- pronostico promedio 24h
- ranking de comunas por MP2.5 predicho

### Vista Tecnica

- metricas del modelo
- real vs predicho
- importancia de variables
- tabla filtrable de predicciones
- distribucion y resumen de clusters

### Vista Ciudadana

- seleccion de comuna
- estado actual
- MP2.5 esperado a 24h
- mensaje simple de alerta

## Ejecucion

```powershell
streamlit run dashboards/app.py
```

O bien:

```powershell
.\scripts\run_dashboard.ps1
```

## Evidencia visual

La carpeta `dashboards/screenshots/` queda preparada para almacenar capturas finales como:

- `vista_ejecutiva.png`
- `vista_tecnica.png`
- `vista_ciudadana.png`
