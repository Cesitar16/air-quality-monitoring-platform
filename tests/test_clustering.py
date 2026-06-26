import numpy as np
import pandas as pd
import pytest

from src.clustering import (
    asignar_etiquetas_riesgo,
    agregar_clusters,
    entrenar_kmeans,
    escalar_variables,
    ejecutar_pipeline_clustering,
    preparar_variables_clustering,
    resumir_clusters,
)


def _crear_dataset_clustering() -> pd.DataFrame:
    filas: list[dict] = []
    perfiles = [
        {
            "base_mp25": 18.0,
            "base_mp10": 35.0,
            "base_so2": 8.0,
            "base_no2": 14.0,
            "base_humedad": 48.0,
            "base_viento": 4.8,
            "base_temp": 16.0,
            "vulnerabilidad": 52.0,
            "emision": 110.0,
            "comuna": "Talca",
            "region": "Maule",
            "sensor": "publico_oficial",
        },
        {
            "base_mp25": 48.0,
            "base_mp10": 85.0,
            "base_so2": 19.0,
            "base_no2": 28.0,
            "base_humedad": 62.0,
            "base_viento": 2.7,
            "base_temp": 11.0,
            "vulnerabilidad": 67.0,
            "emision": 260.0,
            "comuna": "Chillan",
            "region": "Nuble",
            "sensor": "sensor_comunitario_ong",
        },
        {
            "base_mp25": 88.0,
            "base_mp10": 135.0,
            "base_so2": 28.0,
            "base_no2": 42.0,
            "base_humedad": 74.0,
            "base_viento": 1.4,
            "base_temp": 7.0,
            "vulnerabilidad": 79.0,
            "emision": 420.0,
            "comuna": "Los Angeles",
            "region": "Biobio",
            "sensor": "publico_oficial",
        },
    ]

    for indice_perfil, perfil in enumerate(perfiles):
        for paso in range(10):
            filas.append(
                {
                    "fecha_hora": (
                        pd.Timestamp("2026-01-01 00:00:00")
                        + pd.Timedelta(hours=6 * (indice_perfil * 10 + paso))
                    ).isoformat(),
                    "codigo_estacion": f"SEN-TEST-{indice_perfil}-{paso}",
                    "comuna": perfil["comuna"],
                    "region": perfil["region"],
                    "tipo_sensor": perfil["sensor"],
                    "mp25": perfil["base_mp25"] + paso,
                    "mp10": perfil["base_mp10"] + paso * 1.5,
                    "so2": perfil["base_so2"] + (paso % 3),
                    "no2": perfil["base_no2"] + (paso % 4),
                    "temperatura": perfil["base_temp"] - (paso % 2),
                    "humedad": perfil["base_humedad"] + (paso % 4),
                    "velocidad_viento": perfil["base_viento"] - (paso % 2) * 0.2,
                    "emision_maxima_permitida": perfil["emision"],
                    "indice_vulnerabilidad_respiratoria": perfil["vulnerabilidad"],
                }
            )

    dataset = pd.DataFrame(filas)
    dataset.loc[0, "emision_maxima_permitida"] = np.nan
    return dataset


def test_preparar_variables_clustering_imputa_y_devuelve_columnas():
    dataset = _crear_dataset_clustering()

    preparado, columnas = preparar_variables_clustering(dataset)

    assert len(columnas) >= 2
    assert "mp25" in columnas
    assert preparado.isna().sum().sum() == 0


def test_escalar_variables_estandariza_matriz():
    dataset = _crear_dataset_clustering()

    X_scaled, scaler, datos_modelo, columnas = escalar_variables(dataset)

    assert X_scaled.shape[0] == len(dataset)
    assert X_scaled.shape[1] == len(columnas)
    assert scaler.mean_.shape[0] == len(columnas)
    assert np.allclose(np.mean(X_scaled, axis=0), 0.0, atol=1e-7)
    assert not datos_modelo.empty


def test_entrenar_kmeans_y_agregar_clusters():
    dataset = _crear_dataset_clustering()
    X_scaled, _, _, _ = escalar_variables(dataset)

    modelo = entrenar_kmeans(X_scaled, n_clusters=3)
    clusterizado = agregar_clusters(dataset, modelo, X_scaled)

    assert "cluster" in clusterizado.columns
    assert clusterizado["cluster"].nunique() == 3


def test_asignar_etiquetas_riesgo_y_resumen():
    dataset = _crear_dataset_clustering()
    X_scaled, _, _, _ = escalar_variables(dataset)
    modelo = entrenar_kmeans(X_scaled, n_clusters=3)
    clusterizado = agregar_clusters(dataset, modelo, X_scaled)
    etiquetado = asignar_etiquetas_riesgo(clusterizado)
    resumen = resumir_clusters(etiquetado)

    assert "nivel_riesgo" in etiquetado.columns
    assert etiquetado["nivel_riesgo"].notna().all()
    assert {"cluster", "nivel_riesgo", "puntaje_riesgo"}.issubset(resumen.columns)


def test_ejecutar_pipeline_clustering_genera_artefactos(tmp_path):
    dataset_path = tmp_path / "dataset_modelado.csv"
    clusters_path = tmp_path / "clusters.csv"
    summary_path = tmp_path / "resumen.csv"
    model_path = tmp_path / "models" / "kmeans.joblib"
    scaler_path = tmp_path / "models" / "scaler.joblib"
    metrics_path = tmp_path / "models" / "metricas.json"

    _crear_dataset_clustering().to_csv(dataset_path, index=False)

    resultado = ejecutar_pipeline_clustering(
        dataset_path=dataset_path,
        clusters_out=clusters_path,
        summary_out=summary_path,
        model_out=model_path,
        scaler_out=scaler_path,
        metrics_out=metrics_path,
        n_clusters=3,
    )

    clusters = pd.read_csv(clusters_path)
    resumen = pd.read_csv(summary_path)

    assert clusters_path.exists()
    assert summary_path.exists()
    assert model_path.exists()
    assert scaler_path.exists()
    assert metrics_path.exists()
    assert {"cluster", "nivel_riesgo"}.issubset(clusters.columns)
    assert {"cluster", "nivel_riesgo", "puntaje_riesgo"}.issubset(resumen.columns)
    assert resultado.metricas["n_clusters"] == 3
