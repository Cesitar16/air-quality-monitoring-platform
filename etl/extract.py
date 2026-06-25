"""Extraction layer for external air quality data sources."""

from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError

from etl import config


def _validar_archivo_existe(ruta: Path) -> None:
    """Valida que la fuente exista antes de intentar leerla."""
    if not ruta.exists():
        raise FileNotFoundError(f"No existe la fuente requerida: {ruta}")


def _validar_dataframe_no_vacio(df: pd.DataFrame, nombre_fuente: str) -> None:
    """Valida que la fuente cargada tenga al menos una fila."""
    if df.empty:
        raise ValueError(f"La fuente {nombre_fuente} esta vacia.")


def _leer_csv(ruta: Path, nombre_fuente: str) -> pd.DataFrame:
    _validar_archivo_existe(ruta)
    try:
        df = pd.read_csv(ruta)
    except EmptyDataError as exc:
        raise ValueError(f"La fuente {nombre_fuente} esta vacia.") from exc
    _validar_dataframe_no_vacio(df, nombre_fuente)
    return df


def _leer_excel(ruta: Path, nombre_fuente: str) -> pd.DataFrame:
    _validar_archivo_existe(ruta)
    df = pd.read_excel(ruta, engine="openpyxl")
    _validar_dataframe_no_vacio(df, nombre_fuente)
    return df


def extraer_mediciones_oficiales() -> pd.DataFrame:
    """Lee la fuente de mediciones oficiales sin transformar sus datos."""
    return _leer_csv(config.FUENTE_MEDICIONES_OFICIALES, "mediciones_oficiales")


def extraer_sensores_comunitarios() -> pd.DataFrame:
    """Lee la fuente de sensores comunitarios sin transformar sus datos."""
    return _leer_csv(config.FUENTE_SENSORES_COMUNITARIOS, "sensores_comunitarios")


def extraer_fiscalizacion_industrias() -> pd.DataFrame:
    """Lee la fuente de fiscalizacion industrial sin transformar sus datos."""
    return _leer_excel(
        config.FUENTE_FISCALIZACION_INDUSTRIAS,
        "fiscalizacion_industrias",
    )


def extraer_clima_historico() -> pd.DataFrame:
    """Lee la fuente de clima historico sin transformar sus datos."""
    return _leer_csv(config.FUENTE_CLIMA_HISTORICO, "clima_historico")


def extraer_todas_las_fuentes() -> dict[str, pd.DataFrame]:
    """Carga todas las fuentes raw requeridas por la Fase 2."""
    return {
        "mediciones_oficiales": extraer_mediciones_oficiales(),
        "sensores_comunitarios": extraer_sensores_comunitarios(),
        "fiscalizacion_industrias": extraer_fiscalizacion_industrias(),
        "clima_historico": extraer_clima_historico(),
    }
