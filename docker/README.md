# Docker

## Convencion vigente

La entrada oficial de contenedores del proyecto es:

- `docker-compose.yml` en la raiz

La carpeta `docker/` queda reservada unicamente para Dockerfiles reutilizados por ese compose:

- `docker/api.Dockerfile`
- `docker/dashboard.Dockerfile`

No se mantiene un `docker-compose` secundario dentro de esta carpeta para evitar duplicar configuracion y generar drift entre ambientes.

## Como se usa hoy

Levantar base de datos y API:

```powershell
docker compose up --build
```

Levantar tambien el dashboard opcional:

```powershell
docker compose --profile dashboard up --build
```

## Servicios

- `db`: PostgreSQL 16 con schema y seeds del proyecto
- `api`: FastAPI construida desde `docker/api.Dockerfile`
- `dashboard`: Streamlit opcional construido desde `docker/dashboard.Dockerfile`

## Nota operativa

El dashboard consume artefactos generados por ETL y modelamiento, por ejemplo:

- `data/processed/dataset_modelado.csv`
- `data/processed/predicciones_mp25_24h.csv`
- `models/regression/metricas_regresion.json`
- `models/regression/modelo_mp25_24h.joblib`

Si esos archivos no estan actualizados, conviene regenerarlos antes de construir la imagen del dashboard.
