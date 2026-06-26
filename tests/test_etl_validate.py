from pathlib import Path

import pandas as pd
import pytest

from etl.extract import extraer_todas_las_fuentes
from etl.transform import transformar_fuentes
from etl.validate import (
    COLUMNAS_MEDICION_FINAL,
    validar_columnas_requeridas,
    validar_mediciones,
)


def _fila_valida() -> dict:
    return {
        "fecha_hora": pd.Timestamp("2026-06-03 12:00:00"),
        "codigo_estacion": "VAL-001",
        "comuna": "Talca",
        "region": "Maule",
        "mp25": 40.0,
        "mp10": 65.0,
        "so2": 12.0,
        "no2": 18.0,
        "velocidad_viento": 2.5,
        "direccion_viento_grados": 180.0,
        "temperatura": 12.0,
        "humedad": 55.0,
        "fuente_dato": "oficial",
    }


def test_validar_columnas_requeridas_lanza_error_si_falta_columna():
    df = pd.DataFrame(columns=["fecha_hora", "codigo_estacion"])

    with pytest.raises(ValueError, match="mp25"):
        validar_columnas_requeridas(df, COLUMNAS_MEDICION_FINAL)


def test_validar_mediciones_devuelve_todas_validas_y_cero_errores():
    df = pd.DataFrame([_fila_valida()])

    validas, errores = validar_mediciones(df)

    assert len(validas) == 1
    assert errores.empty
    assert list(errores.columns) == list(df.columns) + ["numero_fila", "motivo_error", "fase"]


def test_mp25_negativo_queda_en_errores():
    fila = _fila_valida()
    fila["mp25"] = -1.0
    df = pd.DataFrame([fila])

    validas, errores = validar_mediciones(df)

    assert validas.empty
    assert "mp25 negativo" in errores.iloc[0]["motivo_error"]


def test_humedad_mayor_a_100_queda_en_errores():
    fila = _fila_valida()
    fila["humedad"] = 101.0
    df = pd.DataFrame([fila])

    validas, errores = validar_mediciones(df)

    assert validas.empty
    assert "humedad fuera de rango" in errores.iloc[0]["motivo_error"]


def test_direccion_viento_mayor_a_360_queda_en_errores():
    fila = _fila_valida()
    fila["direccion_viento_grados"] = 361.0
    df = pd.DataFrame([fila])

    validas, errores = validar_mediciones(df)

    assert validas.empty
    assert "direccion_viento_grados fuera de rango" in errores.iloc[0]["motivo_error"]


def test_fecha_hora_nula_queda_en_errores():
    fila = _fila_valida()
    fila["fecha_hora"] = pd.NaT
    df = pd.DataFrame([fila])

    validas, errores = validar_mediciones(df)

    assert validas.empty
    assert "fecha_hora nula" in errores.iloc[0]["motivo_error"]


def test_codigo_estacion_vacio_queda_en_errores():
    fila = _fila_valida()
    fila["codigo_estacion"] = "   "
    df = pd.DataFrame([fila])

    validas, errores = validar_mediciones(df)

    assert validas.empty
    assert "codigo_estacion vacio" in errores.iloc[0]["motivo_error"]


def test_duplicado_deja_primera_valida_y_segunda_invalida():
    fila_a = _fila_valida()
    fila_b = _fila_valida()
    fila_b["mp25"] = 41.0
    df = pd.DataFrame([fila_a, fila_b])

    validas, errores = validar_mediciones(df)

    assert len(validas) == 1
    assert len(errores) == 1
    assert "duplicado codigo_estacion+fecha_hora" in errores.iloc[0]["motivo_error"]


def test_fuente_dato_invalida_queda_en_errores():
    fila = _fila_valida()
    fila["fuente_dato"] = "sensor_privado"
    df = pd.DataFrame([fila])

    validas, errores = validar_mediciones(df)

    assert validas.empty
    assert "fuente_dato invalida" in errores.iloc[0]["motivo_error"]


def test_medicion_valida_con_clima_nan_permanece_valida():
    fila = _fila_valida()
    fila["velocidad_viento"] = float("nan")
    fila["direccion_viento_grados"] = float("nan")
    fila["temperatura"] = float("nan")
    fila["humedad"] = float("nan")
    df = pd.DataFrame([fila])

    validas, errores = validar_mediciones(df)

    assert len(validas) == 1
    assert errores.empty


def test_errores_vacio_mantiene_encabezados_completos():
    df = pd.DataFrame([_fila_valida()])

    _, errores = validar_mediciones(df)

    assert errores.empty
    assert list(errores.columns) == list(df.columns) + ["numero_fila", "motivo_error", "fase"]


def test_validar_mediciones_reales_genera_validas_y_errores():
    fuentes = extraer_todas_las_fuentes()
    transformadas = transformar_fuentes(fuentes)

    validas, errores = validar_mediciones(transformadas["mediciones_limpias"])

    assert len(validas) >= 1
    assert len(errores) >= 1
