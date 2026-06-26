import pandas as pd
import pytest

from etl import config
from etl.extract import (
    extraer_clima_historico,
    extraer_fiscalizacion_industrias,
    extraer_mediciones_oficiales,
    extraer_sensores_comunitarios,
    extraer_todas_las_fuentes,
)


def test_extraer_mediciones_oficiales_devuelve_dataframe_no_vacio():
    df = extraer_mediciones_oficiales()

    assert not df.empty
    assert "fecha_hora" in df.columns


def test_extraer_sensores_comunitarios_devuelve_dataframe_no_vacio():
    df = extraer_sensores_comunitarios()

    assert not df.empty
    assert "codigo_estacion" in df.columns


def test_extraer_fiscalizacion_industrias_devuelve_dataframe_no_vacio():
    df = extraer_fiscalizacion_industrias()

    assert not df.empty
    assert "nombre_industria" in df.columns


def test_extraer_clima_historico_devuelve_dataframe_no_vacio():
    df = extraer_clima_historico()

    assert not df.empty
    assert "humedad" in df.columns


def test_extraer_todas_las_fuentes_devuelve_cuatro_claves():
    fuentes = extraer_todas_las_fuentes()

    assert set(fuentes) == {
        "mediciones_oficiales",
        "sensores_comunitarios",
        "fiscalizacion_industrias",
        "clima_historico",
    }


def test_extraer_mediciones_oficiales_lanza_error_si_falta_archivo(monkeypatch, tmp_path):
    monkeypatch.setattr(
        config,
        "FUENTE_MEDICIONES_OFICIALES",
        tmp_path / "mediciones_inexistentes.csv",
    )

    with pytest.raises(FileNotFoundError, match="mediciones_inexistentes.csv"):
        extraer_mediciones_oficiales()


def test_extraer_sensores_comunitarios_lanza_error_si_csv_esta_vacio(monkeypatch, tmp_path):
    archivo_vacio = tmp_path / "sensores_vacios.csv"
    archivo_vacio.write_text("", encoding="utf-8")
    monkeypatch.setattr(config, "FUENTE_SENSORES_COMUNITARIOS", archivo_vacio)

    with pytest.raises(ValueError, match="sensores_comunitarios"):
        extraer_sensores_comunitarios()


def test_extraer_fiscalizacion_industrias_lanza_error_si_excel_esta_vacio(monkeypatch, tmp_path):
    archivo_vacio = tmp_path / "fiscalizacion_vacia.xlsx"
    pd.DataFrame().to_excel(archivo_vacio, index=False, engine="openpyxl")
    monkeypatch.setattr(config, "FUENTE_FISCALIZACION_INDUSTRIAS", archivo_vacio)

    with pytest.raises(ValueError, match="fiscalizacion_industrias"):
        extraer_fiscalizacion_industrias()


def test_fuentes_reales_conservan_valores_utf8():
    mediciones = extraer_mediciones_oficiales()
    clima = extraer_clima_historico()

    comunas = set(mediciones["comuna"].astype(str)) | set(clima["comuna"].astype(str))
    regiones = set(mediciones["region"].astype(str)) | set(clima["region"].astype(str))

    assert "Chillán" in comunas
    assert "Concepción" in comunas
    assert "Curicó" in comunas
    assert "Ñuble" in regiones
    assert "Biobío" in regiones
