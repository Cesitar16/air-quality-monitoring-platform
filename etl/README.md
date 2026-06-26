# ETL

## Modulos

- `extract.py`
- `transform.py`
- `validate.py`
- `load.py`
- `run_pipeline.py`

## Modos de ejecucion

```powershell
python etl/run_pipeline.py --dry-run
python etl/run_pipeline.py --load-api
```

## Script rapido

```powershell
.\scripts\run_etl.ps1 --load-api
```

## Salidas principales

- `data/processed/mediciones_limpias.csv`
- `data/processed/mediciones_validas.csv`
- `data/processed/errores_etl.csv`
- `data/processed/dataset_modelado.csv`
