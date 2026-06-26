from pathlib import Path
import os

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = ROOT_DIR / "logs"

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_HEALTH_URL = f"{API_BASE_URL}/health"
API_ESTACIONES_URL = f"{API_BASE_URL}/estaciones"
API_COMUNAS_URL = f"{API_BASE_URL}/comunas"
API_MONITOREO_URL = f"{API_BASE_URL}/monitoreo"
API_MONITOREO_BULK_URL = f"{API_BASE_URL}/monitoreo/bulk"
API_DATASET_MODELADO_URL = f"{API_BASE_URL}/analytics/dataset-modelado"

FUENTE_MEDICIONES_OFICIALES = RAW_DIR / "mediciones_oficiales.csv"
FUENTE_SENSORES_COMUNITARIOS = RAW_DIR / "sensores_comunitarios.csv"
FUENTE_FISCALIZACION_INDUSTRIAS = RAW_DIR / "fiscalizacion_industrias.xlsx"
FUENTE_CLIMA_HISTORICO = RAW_DIR / "clima_historico.csv"
FUENTE_MAPEO_ESTACIONES = RAW_DIR / "mapeo_estaciones.csv"

SALIDA_MEDICIONES_LIMPIAS = PROCESSED_DIR / "mediciones_limpias.csv"
SALIDA_MEDICIONES_VALIDAS = PROCESSED_DIR / "mediciones_validas.csv"
SALIDA_INDUSTRIAS_LIMPIAS = PROCESSED_DIR / "industrias_limpias.csv"
SALIDA_CLIMA_LIMPIO = PROCESSED_DIR / "clima_limpio.csv"
SALIDA_ERRORES_ETL = PROCESSED_DIR / "errores_etl.csv"
SALIDA_PAYLOAD_BULK = PROCESSED_DIR / "payload_monitoreo_bulk.json"
SALIDA_REPORTE_CARGA_API = PROCESSED_DIR / "reporte_carga_api.csv"
SALIDA_OMITIDAS_CARGA_API = PROCESSED_DIR / "omitidas_carga_api.csv"
SALIDA_DATASET_MODELADO = PROCESSED_DIR / "dataset_modelado.csv"


def crear_directorios_base() -> None:
    """Create the base directories required by the ETL pipeline."""
    for directory in (RAW_DIR, PROCESSED_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)
