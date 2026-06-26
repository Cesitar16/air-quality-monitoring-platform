# Dashboard

## Objetivo

La app Streamlit consolida historico, clustering y pronosticos de MP2.5.

## Dependencias

```powershell
python -m pip install -r dashboards/requirements.txt
```

## Ejecutar

```powershell
streamlit run dashboards/app.py
```

O bien:

```powershell
.\scripts\run_dashboard.ps1
```

## Artefactos requeridos

- `data/processed/dataset_modelado.csv`
- `data/processed/clusters_riesgo_ambiental.csv`
- `data/processed/resumen_clusters.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/metricas_regresion.json`

La importancia de variables se muestra cuando existe `models/regression/modelo_mp25_24h.joblib`.
