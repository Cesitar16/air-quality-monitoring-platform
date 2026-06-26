"""Training and reporting helpers for the MP2.5 24h regression workflow."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "api"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.calidad_aire_service import clasificar_calidad_aire_mp25  # noqa: E402

DEFAULT_DATASET_PATH = ROOT_DIR / "data" / "processed" / "dataset_modelado.csv"
DEFAULT_MODEL_PATH = ROOT_DIR / "models" / "modelo_mp25_24h.joblib"
DEFAULT_METRICS_PATH = ROOT_DIR / "models" / "metricas_regresion.json"
DEFAULT_PREDICTIONS_PATH = ROOT_DIR / "data" / "processed" / "predicciones_mp25_24h.csv"

TARGET_HORIZON_HOURS = 24
SAMPLING_FREQUENCY_HOURS = 6
TARGET_SHIFT_STEPS = TARGET_HORIZON_HOURS // SAMPLING_FREQUENCY_HOURS
TRAIN_FRACTION = 0.8

REQUIRED_COLUMNS = [
    "fecha_hora",
    "comuna",
    "region",
    "codigo_estacion",
    "tipo_sensor",
    "mp25",
    "mp10",
    "so2",
    "no2",
    "velocidad_viento",
    "direccion_viento_grados",
    "temperatura",
    "humedad",
    "indice_vulnerabilidad_respiratoria",
    "emision_maxima_permitida",
]

NUMERIC_FEATURES = [
    "mp25",
    "mp10",
    "so2",
    "no2",
    "velocidad_viento",
    "direccion_viento_grados",
    "temperatura",
    "humedad",
    "emision_maxima_permitida",
    "indice_vulnerabilidad_respiratoria",
    "hora",
    "dia",
    "mes",
    "dia_semana",
    "lag_1",
    "lag_2",
    "rolling_mean_4",
    "direccion_viento_sin",
    "direccion_viento_cos",
]

CATEGORICAL_FEATURES = [
    "tipo_sensor",
    "comuna",
    "region",
]

PREDICCIONES_COLUMNS = [
    "tipo_registro",
    "fecha_hora_base",
    "fecha_hora_objetivo",
    "codigo_estacion",
    "comuna",
    "region",
    "tipo_sensor",
    "mp25_actual",
    "mp25_real",
    "mp25_predicho",
    "categoria_predicha",
    "mensaje_ciudadano",
    "color_referencial",
]

MOJIBAKE_MARKERS = ("\u00c3", "\u00c2", "\u00e2")


@dataclass
class ResultadoEntrenamiento:
    nombre_modelo: str
    pipeline: Pipeline
    metricas: dict[str, float]
    predicciones_test: np.ndarray


@dataclass
class ResultadoRegresion:
    dataset_entrenamiento: pd.DataFrame
    dataset_features: pd.DataFrame
    train_df: pd.DataFrame
    test_df: pd.DataFrame
    modelos: dict[str, ResultadoEntrenamiento]
    mejor_modelo: str
    metricas: dict[str, Any]
    predicciones: pd.DataFrame


def _asegurar_directorio(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def clasificar_mp25(valor: float) -> dict[str, str]:
    """Expose the same citizen classification used by the API."""
    return clasificar_calidad_aire_mp25(float(valor))


def corregir_texto_mojibake(valor: Any) -> Any:
    """Fix common UTF-8 text that was decoded as latin-1."""
    if not isinstance(valor, str):
        return valor

    texto = " ".join(valor.split())
    if not texto or not any(marker in texto for marker in MOJIBAKE_MARKERS):
        return texto

    try:
        return texto.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return texto


def normalizar_etiquetas_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize visible labels that may arrive with mojibake."""
    df_normalizado = df.copy()
    for columna in ("comuna", "region", "tipo_sensor", "codigo_estacion", "categoria_ica"):
        if columna in df_normalizado.columns:
            df_normalizado[columna] = df_normalizado[columna].apply(corregir_texto_mojibake)
    return df_normalizado


def validar_dataset_modelado(df: pd.DataFrame) -> None:
    """Validate the minimum schema required for training."""
    faltantes = [columna for columna in REQUIRED_COLUMNS if columna not in df.columns]
    if faltantes:
        raise ValueError(
            "Faltan columnas requeridas para regresion: " + ", ".join(faltantes)
        )


def cargar_dataset_modelado(path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Load the modeling dataset from the processed CSV."""
    dataset_path = Path(path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"No existe el dataset de modelado: {dataset_path}")

    df = pd.read_csv(dataset_path)
    df = normalizar_etiquetas_dataset(df)
    validar_dataset_modelado(df)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    if df["fecha_hora"].isna().any():
        raise ValueError("El dataset contiene fechas invalidas en fecha_hora.")
    return df


def preparar_dataset_regresion(
    df: pd.DataFrame,
    target_shift_steps: int = TARGET_SHIFT_STEPS,
) -> pd.DataFrame:
    """Create temporal and historical features without using future information."""
    dataset = df.copy()
    dataset["fecha_hora"] = pd.to_datetime(dataset["fecha_hora"], errors="coerce")
    if dataset["fecha_hora"].isna().any():
        raise ValueError("El dataset contiene fechas invalidas en fecha_hora.")
    dataset = dataset.sort_values(["codigo_estacion", "fecha_hora"]).reset_index(drop=True)

    dataset["hora"] = dataset["fecha_hora"].dt.hour
    dataset["dia"] = dataset["fecha_hora"].dt.day
    dataset["mes"] = dataset["fecha_hora"].dt.month
    dataset["dia_semana"] = dataset["fecha_hora"].dt.dayofweek

    angulo = np.deg2rad(pd.to_numeric(dataset["direccion_viento_grados"], errors="coerce"))
    dataset["direccion_viento_sin"] = np.sin(angulo)
    dataset["direccion_viento_cos"] = np.cos(angulo)

    grupo_estacion = dataset.groupby("codigo_estacion", group_keys=False, sort=False)
    dataset["lag_1"] = grupo_estacion["mp25"].shift(1)
    dataset["lag_2"] = grupo_estacion["mp25"].shift(2)
    dataset["rolling_mean_4"] = grupo_estacion["mp25"].transform(
        lambda serie: serie.shift(1).rolling(window=4, min_periods=1).mean()
    )
    dataset["mp25_24h_futuro"] = grupo_estacion["mp25"].shift(-target_shift_steps)
    dataset["fecha_hora_objetivo"] = dataset["fecha_hora"] + pd.Timedelta(hours=TARGET_HORIZON_HOURS)

    return dataset


def filtrar_dataset_entrenamiento(df: pd.DataFrame) -> pd.DataFrame:
    """Keep rows that have a known target for supervised learning."""
    dataset = df.loc[df["mp25_24h_futuro"].notna()].copy()
    dataset = dataset.sort_values(["fecha_hora", "codigo_estacion"]).reset_index(drop=True)
    if len(dataset) < 2:
        raise ValueError("No hay suficientes filas con objetivo para entrenar el modelo.")
    return dataset


def split_temporal(
    df: pd.DataFrame,
    train_fraction: float = TRAIN_FRACTION,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split the data chronologically without shuffling."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction debe estar entre 0 y 1.")

    dataset = df.sort_values(["fecha_hora", "codigo_estacion"]).reset_index(drop=True)
    split_index = int(len(dataset) * train_fraction)
    split_index = max(1, min(split_index, len(dataset) - 1))

    train_df = dataset.iloc[:split_index].copy()
    test_df = dataset.iloc[split_index:].copy()
    if train_df.empty or test_df.empty:
        raise ValueError("El split temporal produjo un conjunto vacio.")
    return train_df, test_df


def obtener_columnas_features() -> list[str]:
    """Return the feature columns in the same order used by the pipelines."""
    return NUMERIC_FEATURES + CATEGORICAL_FEATURES


def construir_preprocesador() -> ColumnTransformer:
    """Create the shared preprocessing stack for both candidate models."""
    pipeline_numerico = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    pipeline_categorico = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", pipeline_numerico, NUMERIC_FEATURES),
            ("cat", pipeline_categorico, CATEGORICAL_FEATURES),
        ]
    )


def construir_modelos(random_state: int = 42) -> dict[str, Pipeline]:
    """Create the candidate regression pipelines."""
    return {
        "linear_regression": Pipeline(
            steps=[
                ("preprocessor", construir_preprocesador()),
                ("model", LinearRegression()),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                ("preprocessor", construir_preprocesador()),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=300,
                        random_state=random_state,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def entrenar_modelos(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    random_state: int = 42,
) -> dict[str, ResultadoEntrenamiento]:
    """Train and evaluate both candidate models on the same split."""
    modelos = construir_modelos(random_state=random_state)
    columnas_features = obtener_columnas_features()
    x_train = train_df[columnas_features]
    y_train = train_df["mp25_24h_futuro"]
    x_test = test_df[columnas_features]
    y_test = test_df["mp25_24h_futuro"]

    resultados: dict[str, ResultadoEntrenamiento] = {}
    for nombre, pipeline in modelos.items():
        pipeline.fit(x_train, y_train)
        predicciones = pipeline.predict(x_test)
        resultados[nombre] = ResultadoEntrenamiento(
            nombre_modelo=nombre,
            pipeline=pipeline,
            metricas={
                "mae": float(mean_absolute_error(y_test, predicciones)),
                "rmse": float(np.sqrt(mean_squared_error(y_test, predicciones))),
                "r2": float(r2_score(y_test, predicciones)),
            },
            predicciones_test=predicciones,
        )
    return resultados


def seleccionar_mejor_modelo(metricas_por_modelo: dict[str, dict[str, float]]) -> str:
    """Pick the winner using the lowest RMSE."""
    if not metricas_por_modelo:
        raise ValueError("No hay metricas para seleccionar el mejor modelo.")
    return min(metricas_por_modelo, key=lambda nombre: metricas_por_modelo[nombre]["rmse"])


def _aplicar_clasificacion_predicha(predicciones: pd.Series) -> pd.DataFrame:
    clasificaciones = predicciones.apply(lambda valor: clasificar_mp25(float(valor)))
    return pd.DataFrame(clasificaciones.tolist(), index=predicciones.index)


def construir_predicciones_evaluacion(
    test_df: pd.DataFrame,
    predicciones: np.ndarray,
) -> pd.DataFrame:
    """Build the holdout prediction report."""
    base = test_df[
        [
            "fecha_hora",
            "fecha_hora_objetivo",
            "codigo_estacion",
            "comuna",
            "region",
            "tipo_sensor",
            "mp25",
            "mp25_24h_futuro",
        ]
    ].copy()
    base = base.rename(
        columns={
            "fecha_hora": "fecha_hora_base",
            "mp25": "mp25_actual",
            "mp25_24h_futuro": "mp25_real",
        }
    )
    base["tipo_registro"] = "evaluacion"
    base["mp25_predicho"] = predicciones
    clasificacion = _aplicar_clasificacion_predicha(base["mp25_predicho"])
    base["categoria_predicha"] = clasificacion["categoria"]
    base["mensaje_ciudadano"] = clasificacion["mensaje_ciudadano"]
    base["color_referencial"] = clasificacion["color_referencial"]
    return base[PREDICCIONES_COLUMNS]


def construir_pronosticos_24h(
    dataset_features: pd.DataFrame,
    modelo: Pipeline,
) -> pd.DataFrame:
    """Generate 24h forecasts from the latest observation of each station."""
    columnas_features = obtener_columnas_features()
    ultimas_filas = (
        dataset_features.sort_values(["codigo_estacion", "fecha_hora"])
        .groupby("codigo_estacion", as_index=False, group_keys=False)
        .tail(1)
        .copy()
    )
    ultimas_filas["fecha_hora_objetivo"] = ultimas_filas["fecha_hora"] + pd.Timedelta(
        hours=TARGET_HORIZON_HOURS
    )

    predicciones = modelo.predict(ultimas_filas[columnas_features])
    pronosticos = ultimas_filas[
        [
            "fecha_hora",
            "fecha_hora_objetivo",
            "codigo_estacion",
            "comuna",
            "region",
            "tipo_sensor",
            "mp25",
        ]
    ].copy()
    pronosticos = pronosticos.rename(
        columns={
            "fecha_hora": "fecha_hora_base",
            "mp25": "mp25_actual",
        }
    )
    pronosticos["tipo_registro"] = "pronostico_24h"
    pronosticos["mp25_real"] = pd.NA
    pronosticos["mp25_predicho"] = predicciones
    clasificacion = _aplicar_clasificacion_predicha(pronosticos["mp25_predicho"])
    pronosticos["categoria_predicha"] = clasificacion["categoria"]
    pronosticos["mensaje_ciudadano"] = clasificacion["mensaje_ciudadano"]
    pronosticos["color_referencial"] = clasificacion["color_referencial"]
    return pronosticos[PREDICCIONES_COLUMNS]


def guardar_modelo(modelo: Pipeline, path: str | Path = DEFAULT_MODEL_PATH) -> Path:
    """Persist the fitted pipeline."""
    output_path = Path(path)
    _asegurar_directorio(output_path)
    joblib.dump(modelo, output_path)
    return output_path


def cargar_modelo(path: str | Path = DEFAULT_MODEL_PATH) -> Pipeline:
    """Load the fitted regression pipeline."""
    return joblib.load(Path(path))


def guardar_metricas(metricas: dict[str, Any], path: str | Path = DEFAULT_METRICS_PATH) -> Path:
    """Write the training metadata and scores as JSON."""
    output_path = Path(path)
    _asegurar_directorio(output_path)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(metricas, file, ensure_ascii=False, indent=2)
    return output_path


def cargar_metricas(path: str | Path = DEFAULT_METRICS_PATH) -> dict[str, Any]:
    """Load the saved metrics JSON."""
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def guardar_predicciones(
    predicciones: pd.DataFrame,
    path: str | Path = DEFAULT_PREDICTIONS_PATH,
) -> Path:
    """Persist the evaluation and forecast report as CSV."""
    output_path = Path(path)
    _asegurar_directorio(output_path)
    predicciones.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def obtener_importancia_variables(modelo: Pipeline, top_n: int | None = 20) -> pd.DataFrame:
    """Extract comparable feature importance information from the winning pipeline."""
    preprocessor = modelo.named_steps["preprocessor"]
    estimator = modelo.named_steps["model"]
    nombres = [str(nombre).replace("num__", "").replace("cat__", "") for nombre in preprocessor.get_feature_names_out()]

    if hasattr(estimator, "feature_importances_"):
        importancias = np.asarray(estimator.feature_importances_, dtype=float)
    elif hasattr(estimator, "coef_"):
        importancias = np.abs(np.asarray(estimator.coef_, dtype=float).ravel())
    else:
        return pd.DataFrame(columns=["feature", "importance"])

    importancia_df = pd.DataFrame(
        {
            "feature": nombres,
            "importance": importancias,
        }
    ).sort_values("importance", ascending=False, ignore_index=True)

    if top_n is not None:
        return importancia_df.head(top_n).copy()
    return importancia_df


def ejecutar_pipeline_regresion(
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
    model_out: str | Path = DEFAULT_MODEL_PATH,
    metrics_out: str | Path = DEFAULT_METRICS_PATH,
    predictions_out: str | Path = DEFAULT_PREDICTIONS_PATH,
    target_shift_steps: int = TARGET_SHIFT_STEPS,
    train_fraction: float = TRAIN_FRACTION,
) -> ResultadoRegresion:
    """Run the end-to-end regression workflow and persist its artifacts."""
    dataset_modelado = cargar_dataset_modelado(dataset_path)
    dataset_features = preparar_dataset_regresion(
        dataset_modelado,
        target_shift_steps=target_shift_steps,
    )
    dataset_entrenamiento = filtrar_dataset_entrenamiento(dataset_features)
    train_df, test_df = split_temporal(dataset_entrenamiento, train_fraction=train_fraction)

    modelos = entrenar_modelos(train_df, test_df)
    metricas_por_modelo = {
        nombre: resultado.metricas for nombre, resultado in modelos.items()
    }
    mejor_modelo = seleccionar_mejor_modelo(metricas_por_modelo)
    mejor_pipeline = modelos[mejor_modelo].pipeline

    predicciones_evaluacion = construir_predicciones_evaluacion(
        test_df,
        modelos[mejor_modelo].predicciones_test,
    )
    predicciones_pronostico = construir_pronosticos_24h(dataset_features, mejor_pipeline)
    predicciones = pd.concat(
        [predicciones_evaluacion, predicciones_pronostico],
        ignore_index=True,
    )

    metricas = {
        "horizon_hours": TARGET_HORIZON_HOURS,
        "sampling_frequency_hours": SAMPLING_FREQUENCY_HOURS,
        "target_shift_steps": target_shift_steps,
        "train_rows": int(len(train_df)),
        "test_rows": int(len(test_df)),
        "best_model": mejor_modelo,
        "models": metricas_por_modelo,
    }

    guardar_modelo(mejor_pipeline, model_out)
    guardar_metricas(metricas, metrics_out)
    guardar_predicciones(predicciones, predictions_out)

    return ResultadoRegresion(
        dataset_entrenamiento=dataset_entrenamiento,
        dataset_features=dataset_features,
        train_df=train_df,
        test_df=test_df,
        modelos=modelos,
        mejor_modelo=mejor_modelo,
        metricas=metricas,
        predicciones=predicciones,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Entrena la regresion MP2.5 a 24 horas.")
    parser.add_argument("--dataset", default=str(DEFAULT_DATASET_PATH))
    parser.add_argument("--model-out", default=str(DEFAULT_MODEL_PATH))
    parser.add_argument("--metrics-out", default=str(DEFAULT_METRICS_PATH))
    parser.add_argument("--predictions-out", default=str(DEFAULT_PREDICTIONS_PATH))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    resultado = ejecutar_pipeline_regresion(
        dataset_path=args.dataset,
        model_out=args.model_out,
        metrics_out=args.metrics_out,
        predictions_out=args.predictions_out,
    )

    print("[Regression] Dataset entrenamiento:", len(resultado.dataset_entrenamiento))
    print("[Regression] Train:", len(resultado.train_df))
    print("[Regression] Test:", len(resultado.test_df))
    print("[Regression] Mejor modelo:", resultado.mejor_modelo)
    print("[Regression] Predicciones generadas:", len(resultado.predicciones))
    print("[Regression] Modelo guardado en:", Path(args.model_out))
    print("[Regression] Metricas guardadas en:", Path(args.metrics_out))
    print("[Regression] Predicciones guardadas en:", Path(args.predictions_out))


if __name__ == "__main__":
    main()
