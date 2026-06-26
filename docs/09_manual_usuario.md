# 09 - Manual de Usuario

## 1. Preparar entorno

```powershell
python -m pip install -r requirements.txt
```

Para ejecutar solo el dashboard:

```powershell
python -m pip install -r dashboards/requirements.txt
```

## 2. Levantar servicios base

```powershell
docker compose up --build
```

## 3. Ejecutar ETL

Modo local:

```powershell
python etl/run_pipeline.py --dry-run
```

Modo integrado con API:

```powershell
python etl/run_pipeline.py --load-api
```

## 4. Ejecutar clustering

```powershell
python src/clustering.py
```

## 5. Ejecutar regresion

```powershell
python src/regression.py
```

## 6. Ejecutar dashboard

```powershell
streamlit run dashboards/app.py
```

## 7. Ejecutar pruebas

```powershell
python -m pytest -q
```

El reporte automatizado se guarda en:

- `tests/reports/pytest_result.txt`

## 8. Scripts rapidos

```powershell
.\scripts\run_etl.ps1 --load-api
.\scripts\run_clustering.ps1
.\scripts\run_regression.ps1
.\scripts\run_dashboard.ps1
.\scripts\run_tests.ps1
```

## 9. Limitaciones conocidas

- el dashboard requiere que clustering y regresion ya hayan generado artefactos
- el modelo de regresion depende de que `dataset_modelado.csv` tenga continuidad temporal por estacion
- para Python 3.14 puede ser preferible usar Docker o Python 3.12/3.13 por la dependencia PostgreSQL
