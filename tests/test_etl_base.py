import pandas as pd
import pytest

from etl import config
from etl.transform import normalizar_columnas
from etl.validate import validar_columnas_requeridas


def test_crear_directorios_base_crea_rutas_esperadas(monkeypatch, tmp_path):
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    logs_dir = tmp_path / "logs"

    monkeypatch.setattr(config, "RAW_DIR", raw_dir)
    monkeypatch.setattr(config, "PROCESSED_DIR", processed_dir)
    monkeypatch.setattr(config, "LOGS_DIR", logs_dir)

    config.crear_directorios_base()

    assert raw_dir.exists()
    assert processed_dir.exists()
    assert logs_dir.exists()


def test_normalizar_columnas_normaliza_nombres():
    df = pd.DataFrame(columns=[" Fecha Hora ", "MP25", "Codigo Estacion"])

    df_normalizado = normalizar_columnas(df)

    assert list(df_normalizado.columns) == ["fecha_hora", "mp25", "codigo_estacion"]
    assert list(df.columns) == [" Fecha Hora ", "MP25", "Codigo Estacion"]


def test_validar_columnas_requeridas_no_falla_si_estan_todas():
    df = pd.DataFrame(columns=["fecha_hora", "codigo_estacion", "mp25"])

    validar_columnas_requeridas(df, ["fecha_hora", "codigo_estacion"])


def test_validar_columnas_requeridas_lanza_error_si_falta_una():
    df = pd.DataFrame(columns=["fecha_hora", "mp25"])

    with pytest.raises(ValueError, match="codigo_estacion"):
        validar_columnas_requeridas(df, ["fecha_hora", "codigo_estacion"])
