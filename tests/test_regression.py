import pandas as pd
import pytest

from src.regression import (
    TARGET_SHIFT_STEPS,
    TARGET_COLUMN,
    cargar_dataset_modelado,
    cargar_modelo,
    clasificar_mp25,
    ejecutar_pipeline_regresion,
    entrenar_modelos,
    filtrar_dataset_entrenamiento,
    guardar_modelo,
    obtener_columnas_features,
    obtener_importancia_variables,
    preparar_dataset_regresion,
    seleccionar_mejor_modelo,
    split_temporal,
    validar_dataset_modelado,
)


def _crear_dataset_modelado(rows_per_station: int = 18) -> pd.DataFrame:
    inicio = pd.Timestamp("2026-01-01 00:00:00")
    estaciones = [
        ("SEN-TAL-OF-001", "Talca", "Maule", "publico_oficial", 420.0, 64.2),
        (
            "SEN-CON-ONG-001",
            "Concepci\u00c3\u00b3n",
            "Biob\u00c3\u00ado",
            "sensor_comunitario_ong",
            390.0,
            69.5,
        ),
        (
            "SEN-CHI-OF-001",
            "Chill\u00c3\u00a1n",
            "\u00c3\u0091uble",
            "publico_oficial",
            180.0,
            72.8,
        ),
    ]

    filas: list[dict] = []
    for indice_estacion, (
        codigo_estacion,
        comuna,
        region,
        tipo_sensor,
        emision_maxima,
        vulnerabilidad,
    ) in enumerate(estaciones):
        for paso in range(rows_per_station):
            fecha = inicio + pd.Timedelta(hours=6 * paso)
            viento = 1.4 + (paso % 4) * 0.5 + indice_estacion * 0.1
            temperatura = 7.0 + (paso % 6) + indice_estacion
            humedad = 52.0 + (paso % 5) * 3 + indice_estacion
            so2 = 11.0 + indice_estacion * 4 + (paso % 3)
            no2 = 18.0 + indice_estacion * 5 + (paso % 4)
            mp10 = 42.0 + paso * 1.7 + indice_estacion * 4
            mp25 = round(
                0.42 * mp10
                + 0.11 * no2
                - 0.35 * viento
                + 0.07 * humedad
                + indice_estacion
                + (paso % 4) * 1.2,
                2,
            )
            filas.append(
                {
                    "fecha_hora": fecha.isoformat(),
                    "comuna": comuna,
                    "region": region,
                    "codigo_estacion": codigo_estacion,
                    "tipo_sensor": tipo_sensor,
                    "mp25": mp25,
                    "mp10": round(mp10, 2),
                    "so2": round(so2, 2),
                    "no2": round(no2, 2),
                    "velocidad_viento": round(viento, 2),
                    "direccion_viento_grados": float((45 + paso * 15 + indice_estacion * 20) % 360),
                    "temperatura": round(temperatura, 2),
                    "humedad": round(humedad, 2),
                    "indice_vulnerabilidad_respiratoria": vulnerabilidad,
                    "emision_maxima_permitida": emision_maxima
                    if paso % 7 != 0
                    else float("nan"),
                    "categoria_ica": clasificar_mp25(mp25)["categoria"],
                }
            )
    return pd.DataFrame(filas)


def test_validar_dataset_modelado_lanza_error_si_falta_columna():
    df = pd.DataFrame(columns=["fecha_hora", "comuna"])

    with pytest.raises(ValueError, match="mp25"):
        validar_dataset_modelado(df)


def test_cargar_dataset_modelado_corrige_mojibake(tmp_path):
    dataset_path = tmp_path / "dataset_modelado.csv"
    _crear_dataset_modelado(rows_per_station=4).to_csv(dataset_path, index=False)

    df = cargar_dataset_modelado(dataset_path)

    assert "Concepci\u00f3n" in set(df["comuna"])
    assert "Biob\u00edo" in set(df["region"])
    assert "Chill\u00e1n" in set(df["comuna"])


def test_cargar_dataset_modelado_completa_columnas_faltantes_del_dry_run(tmp_path):
    dataset_path = tmp_path / "dataset_modelado.csv"
    df = _crear_dataset_modelado(rows_per_station=4).drop(
        columns=[
            "tipo_sensor",
            "indice_vulnerabilidad_respiratoria",
            "emision_maxima_permitida",
        ]
    )
    df["fuente_dato"] = "oficial"
    df.to_csv(dataset_path, index=False)

    cargado = cargar_dataset_modelado(dataset_path)

    assert "tipo_sensor" in cargado.columns
    assert "indice_vulnerabilidad_respiratoria" in cargado.columns
    assert "emision_maxima_permitida" in cargado.columns
    assert set(cargado["tipo_sensor"]) == {"publico_oficial", "sensor_comunitario_ong"}


def test_preparar_dataset_regresion_construye_target_y_lags_sin_fuga():
    df = pd.DataFrame(
        [
            {
                "fecha_hora": pd.Timestamp("2026-01-01 00:00:00") + pd.Timedelta(hours=6 * paso),
                "comuna": "Talca",
                "region": "Maule",
                "codigo_estacion": "SEN-TAL-OF-001",
                "tipo_sensor": "publico_oficial",
                "mp25": valor,
                "mp10": valor + 10,
                "so2": 10.0,
                "no2": 20.0,
                "velocidad_viento": 2.0,
                "direccion_viento_grados": 180.0,
                "temperatura": 12.0,
                "humedad": 60.0,
                "indice_vulnerabilidad_respiratoria": 64.2,
                "emision_maxima_permitida": 420.0,
            }
            for paso, valor in enumerate([10.0, 20.0, 30.0, 40.0, 50.0, 60.0])
        ]
    )

    preparado = preparar_dataset_regresion(df, target_shift_steps=4)

    assert preparado.loc[0, TARGET_COLUMN] == 50.0
    assert preparado.loc[1, TARGET_COLUMN] == 60.0
    assert preparado.loc[0, "mp25_24h_futuro"] == 50.0
    assert preparado.loc[2, "lag_1"] == 20.0
    assert preparado.loc[2, "lag_2"] == 10.0
    assert preparado.loc[3, "lag_3"] == 10.0
    assert preparado.loc[2, "delta_mp25"] == 10.0
    assert preparado.loc[2, "mp25_promedio_movil_3"] == 15.0
    assert preparado.loc[2, "rolling_mean_6"] == 15.0
    assert preparado.loc[2, "rolling_mean_12"] == 15.0
    assert preparado.loc[0, "estacion_del_ano"] == "verano"
    assert preparado.loc[0, "fecha_hora_objetivo"] == pd.Timestamp("2026-01-02 00:00:00")


def test_preparar_dataset_regresion_hace_fallback_por_comuna_si_estacion_no_alcanza():
    filas = []
    tiempos_a = [0, 12, 24, 36]
    tiempos_b = [6, 18, 30, 42]

    for indice, hora in enumerate(tiempos_a):
        filas.append(
            {
                "fecha_hora": pd.Timestamp("2026-01-01 00:00:00") + pd.Timedelta(hours=hora),
                "comuna": "Talca",
                "region": "Maule",
                "codigo_estacion": "STA-A",
                "tipo_sensor": "publico_oficial",
                "mp25": 10.0 + indice,
                "mp10": 20.0 + indice,
                "so2": 5.0,
                "no2": 10.0,
                "velocidad_viento": 2.0,
                "direccion_viento_grados": 90.0,
                "temperatura": 12.0,
                "humedad": 60.0,
                "indice_vulnerabilidad_respiratoria": 64.2,
                "emision_maxima_permitida": 420.0,
            }
        )

    for indice, hora in enumerate(tiempos_b):
        filas.append(
            {
                "fecha_hora": pd.Timestamp("2026-01-01 00:00:00") + pd.Timedelta(hours=hora),
                "comuna": "Talca",
                "region": "Maule",
                "codigo_estacion": "STA-B",
                "tipo_sensor": "sensor_comunitario_ong",
                "mp25": 20.0 + indice,
                "mp10": 30.0 + indice,
                "so2": 6.0,
                "no2": 12.0,
                "velocidad_viento": 2.5,
                "direccion_viento_grados": 180.0,
                "temperatura": 11.0,
                "humedad": 62.0,
                "indice_vulnerabilidad_respiratoria": 64.2,
                "emision_maxima_permitida": 420.0,
            }
        )

    preparado = preparar_dataset_regresion(pd.DataFrame(filas), target_shift_steps=4)

    fila_a = preparado.loc[preparado["codigo_estacion"] == "STA-A"].sort_values("fecha_hora").iloc[0]
    assert pd.notna(fila_a[TARGET_COLUMN])
    assert pd.isna(fila_a["mp25_24h_estacion"])
    assert pd.notna(fila_a["mp25_24h_comuna"])


def test_entrenar_modelos_devuelve_metricas_para_ambos():
    dataset = preparar_dataset_regresion(_crear_dataset_modelado())
    entrenamiento = filtrar_dataset_entrenamiento(dataset)
    train_df, test_df = split_temporal(entrenamiento)

    resultados = entrenar_modelos(train_df, test_df)

    assert set(resultados) == {"linear_regression", "random_forest"}
    for resultado in resultados.values():
        assert {"mae", "rmse", "r2"} == set(resultado.metricas)
        assert len(resultado.predicciones_test) == len(test_df)


def test_seleccionar_mejor_modelo_por_rmse():
    metricas = {
        "linear_regression": {"mae": 4.0, "rmse": 5.0, "r2": 0.8},
        "random_forest": {"mae": 3.0, "rmse": 4.1, "r2": 0.82},
    }

    assert seleccionar_mejor_modelo(metricas) == "random_forest"


def test_guardar_y_cargar_modelo(tmp_path):
    dataset = preparar_dataset_regresion(_crear_dataset_modelado())
    entrenamiento = filtrar_dataset_entrenamiento(dataset)
    train_df, test_df = split_temporal(entrenamiento)
    resultados = entrenar_modelos(train_df, test_df)
    modelo = resultados["linear_regression"].pipeline
    model_path = tmp_path / "modelo.joblib"

    guardar_modelo(modelo, model_path)
    modelo_cargado = cargar_modelo(model_path)
    muestra = test_df.iloc[:3]
    predicciones = modelo_cargado.predict(muestra[obtener_columnas_features()])

    assert model_path.exists()
    assert len(predicciones) == 3


def test_ejecutar_pipeline_regresion_genera_artefactos_y_predicciones(tmp_path):
    dataset_path = tmp_path / "dataset_modelado.csv"
    model_path = tmp_path / "modelo_mp25_24h.joblib"
    metrics_path = tmp_path / "metricas_regresion.json"
    predictions_path = tmp_path / "predicciones_mp25_24h.csv"

    _crear_dataset_modelado().to_csv(dataset_path, index=False)

    resultado = ejecutar_pipeline_regresion(
        dataset_path=dataset_path,
        model_out=model_path,
        metrics_out=metrics_path,
        predictions_out=predictions_path,
        target_shift_steps=TARGET_SHIFT_STEPS,
    )

    predicciones = pd.read_csv(predictions_path)
    importancia_df = obtener_importancia_variables(
        resultado.modelos[resultado.mejor_modelo].pipeline,
        top_n=5,
    )

    assert model_path.exists()
    assert metrics_path.exists()
    assert predictions_path.exists()
    assert set(predicciones["tipo_registro"]) == {"evaluacion", "pronostico_24h"}
    assert {
        "fecha_hora",
        "mp25_real_24h",
        "mp25_predicho_24h",
        "error_absoluto",
        "categoria_alerta_predicha",
    }.issubset(predicciones.columns)
    assert len(
        predicciones.loc[predicciones["tipo_registro"] == "pronostico_24h", "codigo_estacion"].unique()
    ) == 3
    assert resultado.metricas["best_model"] in {"linear_regression", "random_forest"}
    assert "time_series_cv" in resultado.metricas
    assert "estacion_del_ano" in resultado.metricas["features_used"]
    assert not importancia_df.empty
