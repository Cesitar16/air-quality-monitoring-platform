import json
import os
import subprocess
import sys

import pandas as pd
import pytest

from etl import config
from etl.load import (
    MAPEO_ESTACIONES_COLUMNS,
    OMITIDAS_COLUMNS,
    cargar_mediciones_bulk,
    construir_indices_estaciones,
    construir_mapa_estaciones,
    construir_mapa_manual_estaciones,
    filtrar_mediciones_existentes,
    guardar_dataset_modelado,
    guardar_omitidas_carga,
    guardar_payload_bulk,
    guardar_reporte_carga,
    leer_mapeo_estaciones,
    preparar_payload_bulk,
    resolver_ids_estaciones_api,
    verificar_api_disponible,
)
from etl.run_pipeline import main


def _fila_medicion(**overrides):
    base = {
        "fecha_hora": "2026-06-20 08:00:00",
        "codigo_estacion": "OF-TAL-001",
        "comuna": "Talca",
        "region": "Maule",
        "mp25": 55.2,
        "mp10": 90.4,
        "so2": 10.5,
        "no2": 15.1,
        "velocidad_viento": 2.7,
        "direccion_viento_grados": 180.0,
        "temperatura": 10.2,
        "humedad": 62.0,
        "fuente_dato": "oficial",
    }
    base.update(overrides)
    return base


def test_verificar_api_disponible_retorna_false_si_api_no_esta(monkeypatch):
    def fake_get(*args, **kwargs):
        raise RuntimeError("sin api")

    monkeypatch.setattr("etl.load.requests.get", fake_get)

    assert verificar_api_disponible() is False


def test_leer_mapeo_estaciones_valido(tmp_path, monkeypatch):
    ruta = tmp_path / "mapeo_estaciones.csv"
    ruta.write_text(
        "codigo_estacion_raw,codigo_unico_api,comuna,region,fuente_dato,tipo_sensor_api\n"
        "OF-TAL-001,SEN-TAL-OF-001,Talca,Maule,oficial,publico_oficial\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "FUENTE_MAPEO_ESTACIONES", ruta)

    df = leer_mapeo_estaciones()

    assert list(df.columns) == MAPEO_ESTACIONES_COLUMNS
    assert df.iloc[0]["codigo_unico_api"] == "SEN-TAL-OF-001"


def test_leer_mapeo_estaciones_falla_si_faltan_columnas(tmp_path, monkeypatch):
    ruta = tmp_path / "mapeo_estaciones.csv"
    ruta.write_text(
        "codigo_estacion_raw,codigo_unico_api\nOF-TAL-001,SEN-TAL-OF-001\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "FUENTE_MAPEO_ESTACIONES", ruta)

    with pytest.raises(ValueError, match="Faltan columnas requeridas"):
        leer_mapeo_estaciones()


def test_leer_mapeo_estaciones_falla_si_hay_codigos_raw_duplicados(tmp_path, monkeypatch):
    ruta = tmp_path / "mapeo_estaciones.csv"
    ruta.write_text(
        "codigo_estacion_raw,codigo_unico_api,comuna,region,fuente_dato,tipo_sensor_api\n"
        "OF-TAL-001,SEN-TAL-OF-001,Talca,Maule,oficial,publico_oficial\n"
        "OF-TAL-001,SEN-TAL-OF-002,Talca,Maule,oficial,publico_oficial\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(config, "FUENTE_MAPEO_ESTACIONES", ruta)

    with pytest.raises(ValueError, match="duplicados"):
        leer_mapeo_estaciones()


def test_construir_mapa_estaciones_desde_lista_simulada():
    estaciones = [
        {"codigo_unico": "SEN-TAL-OF-001", "id_estacion": 1},
        {"codigo_estacion": "SEN-CHI-ONG-001", "id_estacion": 2},
        {"codigo_unico": None, "id_estacion": 3},
    ]

    mapa = construir_mapa_estaciones(estaciones)

    assert mapa == {"SEN-TAL-OF-001": 1, "SEN-CHI-ONG-001": 2}


def test_construir_mapa_manual_estaciones_y_resolver_ids():
    df_mapeo = pd.DataFrame(
        [
            {
                "codigo_estacion_raw": "OF-TAL-001",
                "codigo_unico_api": "SEN-TAL-OF-001",
                "comuna": "Talca",
                "region": "Maule",
                "fuente_dato": "oficial",
                "tipo_sensor_api": "publico_oficial",
            }
        ]
    )
    estaciones = [{"codigo_unico": "SEN-TAL-OF-001", "id_estacion": 7}]

    mapa_manual = construir_mapa_manual_estaciones(df_mapeo)
    resolucion = resolver_ids_estaciones_api(df_mapeo, estaciones)

    assert mapa_manual == {"OF-TAL-001": "SEN-TAL-OF-001"}
    assert resolucion["OF-TAL-001"]["id_estacion"] == 7


def test_preparar_payload_bulk_respeta_precedencia_exacto_sobre_csv_y_heuristica():
    df = pd.DataFrame([_fila_medicion(codigo_estacion="SEN-TAL-OF-001")])
    mapa_exacto = {"SEN-TAL-OF-001": 1}
    mapa_manual = {
        "SEN-TAL-OF-001": {
            "codigo_unico_api": "SEN-TAL-OF-001",
            "id_estacion": 99,
            "comuna": "Talca",
            "region": "Maule",
            "fuente_dato": "oficial",
            "tipo_sensor_api": "publico_oficial",
        }
    }
    indice_heuristico = {
        ("Talca", "publico_oficial"): [
            {
                "id_estacion": 55,
                "codigo_unico_api": "SEN-TAL-OF-999",
                "tipo_sensor": "publico_oficial",
                "comuna": "Talca",
            }
        ]
    }

    payload, omitidas = preparar_payload_bulk(
        df,
        mapa_exacto,
        mapa_manual_resuelto=mapa_manual,
        indice_heuristico=indice_heuristico,
    )

    assert len(payload) == 1
    assert payload[0]["id_estacion"] == 1
    assert payload[0]["_modo_mapeo"] == "exacto_api"
    assert omitidas.empty


def test_preparar_payload_bulk_usa_mapeo_manual_si_no_hay_match_exacto():
    df = pd.DataFrame([_fila_medicion()])
    mapa_manual = {
        "OF-TAL-001": {
            "codigo_unico_api": "SEN-TAL-OF-001",
            "id_estacion": 8,
            "comuna": "Talca",
            "region": "Maule",
            "fuente_dato": "oficial",
            "tipo_sensor_api": "publico_oficial",
        }
    }

    payload, omitidas = preparar_payload_bulk(
        df,
        mapa_estaciones_api={},
        mapa_manual_resuelto=mapa_manual,
        indice_heuristico={},
    )

    assert len(payload) == 1
    assert payload[0]["id_estacion"] == 8
    assert payload[0]["_modo_mapeo"] == "mapeo_manual_csv"
    assert omitidas.empty


def test_preparar_payload_bulk_omite_fila_si_falta_clima_requerido_por_api():
    df = pd.DataFrame([_fila_medicion(velocidad_viento=None)])
    mapa_manual = {
        "OF-TAL-001": {
            "codigo_unico_api": "SEN-TAL-OF-001",
            "id_estacion": 8,
            "comuna": "Talca",
            "region": "Maule",
            "fuente_dato": "oficial",
            "tipo_sensor_api": "publico_oficial",
        }
    }

    payload, omitidas = preparar_payload_bulk(
        df,
        mapa_estaciones_api={},
        mapa_manual_resuelto=mapa_manual,
        indice_heuristico={},
    )

    assert payload == []
    assert len(omitidas) == 1
    assert omitidas.iloc[0]["motivo_omision"] == "clima_requerido_por_api"
    assert omitidas.iloc[0]["id_estacion"] == 8


def test_preparar_payload_bulk_omite_codigo_api_no_disponible():
    df = pd.DataFrame([_fila_medicion()])
    mapa_manual = {
        "OF-TAL-001": {
            "codigo_unico_api": "SEN-TAL-OF-001",
            "id_estacion": None,
            "comuna": "Talca",
            "region": "Maule",
            "fuente_dato": "oficial",
            "tipo_sensor_api": "publico_oficial",
        }
    }

    payload, omitidas = preparar_payload_bulk(
        df,
        mapa_estaciones_api={},
        mapa_manual_resuelto=mapa_manual,
        indice_heuristico={},
    )

    assert payload == []
    assert len(omitidas) == 1
    assert omitidas.iloc[0]["motivo_omision"] == "codigo_api_no_disponible"
    assert omitidas.iloc[0]["modo_mapeo"] == "mapeo_manual_csv"


def test_preparar_payload_bulk_omite_estacion_ambigua_por_heuristica():
    df = pd.DataFrame([_fila_medicion()])
    indice_heuristico = {
        ("Talca", "publico_oficial"): [
            {
                "id_estacion": 8,
                "codigo_unico_api": "SEN-TAL-OF-001",
                "tipo_sensor": "publico_oficial",
                "comuna": "Talca",
            },
            {
                "id_estacion": 9,
                "codigo_unico_api": "SEN-TAL-OF-002",
                "tipo_sensor": "publico_oficial",
                "comuna": "Talca",
            },
        ]
    }

    payload, omitidas = preparar_payload_bulk(
        df,
        mapa_estaciones_api={},
        mapa_manual_resuelto={},
        indice_heuristico=indice_heuristico,
    )

    assert payload == []
    assert len(omitidas) == 1
    assert omitidas.iloc[0]["motivo_omision"] == "estacion_ambigua"


def test_filtrar_mediciones_existentes_omite_duplicados_api(monkeypatch):
    payload = [
        {
            "fecha_hora": "2026-06-20T08:00:00",
            "id_estacion": 1,
            "mp25": 55.2,
            "mp10": 90.4,
            "so2": 10.5,
            "no2": 15.1,
            "velocidad_viento": 2.7,
            "direccion_viento_grados": 180.0,
            "temperatura": 10.2,
            "humedad": 62.0,
            "_codigo_estacion": "OF-TAL-001",
            "_codigo_unico_api": "SEN-TAL-OF-001",
            "_comuna": "Talca",
            "_region": "Maule",
            "_fuente_dato": "oficial",
            "_modo_mapeo": "mapeo_manual_csv",
        }
    ]

    monkeypatch.setattr(
        "etl.load.obtener_mediciones_api",
        lambda *args, **kwargs: [{"id_estacion": 1, "fecha_hora": "2026-06-20T08:00:00"}],
    )

    nuevas, omitidas = filtrar_mediciones_existentes(payload, strict=True)

    assert nuevas == []
    assert len(omitidas) == 1
    assert omitidas.iloc[0]["motivo_omision"] == "medicion_ya_existente"


def test_guardar_payload_bulk_crea_archivo_json_sin_metadata():
    payload = [
        {
            "fecha_hora": "2026-06-20T08:00:00",
            "id_estacion": 1,
            "mp25": 55.2,
            "_codigo_estacion": "OF-TAL-001",
        }
    ]

    guardar_payload_bulk(payload)

    assert config.SALIDA_PAYLOAD_BULK.exists()
    contenido = json.loads(config.SALIDA_PAYLOAD_BULK.read_text(encoding="utf-8"))
    assert contenido["mediciones"][0]["id_estacion"] == 1
    assert "_codigo_estacion" not in contenido["mediciones"][0]


def test_cargar_mediciones_bulk_dry_run_no_llama_api():
    payload = [{"id_estacion": 1}]

    respuesta = cargar_mediciones_bulk(payload, dry_run=True)

    assert respuesta["modo"] == "dry-run"
    assert respuesta["total_preparadas"] == 1


def test_cargar_mediciones_bulk_no_llama_api_si_payload_vacio_en_load_api():
    respuesta = cargar_mediciones_bulk([], dry_run=False)

    assert respuesta["modo"] == "api"
    assert respuesta["insertados"] == 0
    assert respuesta["errores"] == 0
    assert respuesta["mensaje"] == "No hay mediciones nuevas compatibles para enviar a la API."


def test_guardar_reporte_carga_genera_csv_con_nuevas_metricas():
    respuesta = {
        "modo": "dry-run",
        "total_preparadas": 2,
        "total_con_id_estacion": 1,
        "insertados": 0,
        "errores": 0,
        "mensaje": "ok",
        "modo_mapeo": "exacto_api>mapeo_manual_csv>heuristico_seguro",
    }
    omitidas = pd.DataFrame(
        [
            {
                "codigo_estacion": "OF-TAL-001",
                "codigo_unico_api": "SEN-TAL-OF-001",
                "id_estacion": 1,
                "comuna": "Talca",
                "region": "Maule",
                "fuente_dato": "oficial",
                "fecha_hora": "2026-06-20 08:00:00",
                "motivo_omision": "clima_requerido_por_api",
                "modo_mapeo": "mapeo_manual_csv",
            }
        ]
    )

    guardar_reporte_carga(respuesta, omitidas=omitidas)

    assert config.SALIDA_REPORTE_CARGA_API.exists()
    df = pd.read_csv(config.SALIDA_REPORTE_CARGA_API)
    assert df.iloc[0]["omitidas_por_clima_requerido_api"] == 1


def test_guardar_reporte_carga_deja_mensaje_payload_vacio():
    respuesta = {
        "modo": "api",
        "total_preparadas": 0,
        "total_con_id_estacion": 3,
        "insertados": 0,
        "errores": 0,
        "mensaje": "No hay mediciones nuevas compatibles para enviar a la API.",
    }

    guardar_reporte_carga(respuesta, omitidas=pd.DataFrame(columns=OMITIDAS_COLUMNS))

    df = pd.read_csv(config.SALIDA_REPORTE_CARGA_API)
    assert df.iloc[0]["insertados"] == 0
    assert df.iloc[0]["errores"] == 0
    assert (
        df.iloc[0]["mensaje"]
        == "No hay mediciones nuevas compatibles para enviar a la API."
    )


def test_guardar_dataset_modelado_dry_run_genera_dataset_local():
    df = guardar_dataset_modelado(dry_run=True)

    assert config.SALIDA_DATASET_MODELADO.exists()
    assert not df.empty


def test_run_pipeline_dry_run_genera_payload_reporte_y_dataset():
    main(["--dry-run"])

    assert config.SALIDA_PAYLOAD_BULK.exists()
    assert config.SALIDA_OMITIDAS_CARGA_API.exists()
    assert config.SALIDA_REPORTE_CARGA_API.exists()
    assert config.SALIDA_DATASET_MODELADO.exists()


def test_run_pipeline_load_api_falla_si_api_no_esta(monkeypatch):
    monkeypatch.setattr("etl.run_pipeline.verificar_api_disponible", lambda: False)

    with pytest.raises(RuntimeError, match="La API no esta disponible"):
        main(["--load-api"])


def test_run_pipeline_cli_usa_realmente_los_argumentos():
    command = [
        sys.executable,
        "etl/run_pipeline.py",
        "--load-api",
    ]
    env = os.environ.copy()
    env["ETL_DRY_RUN"] = ""
    env["API_BASE_URL"] = "http://127.0.0.1:9"

    result = subprocess.run(
        command,
        cwd=str(config.ROOT_DIR),
        capture_output=True,
        text=True,
        env=env,
    )

    assert result.returncode != 0
    assert "La API no esta disponible para --load-api" in (result.stdout + result.stderr)
    assert "Modo dry-run activo" not in (result.stdout + result.stderr)


def test_guardar_omitidas_carga_genera_csv_vacio_con_encabezados():
    guardar_omitidas_carga(pd.DataFrame(columns=OMITIDAS_COLUMNS))

    df = pd.read_csv(config.SALIDA_OMITIDAS_CARGA_API)
    assert list(df.columns) == OMITIDAS_COLUMNS
