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
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import TimeSeriesSplit

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "api"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

from app.services.calidad_aire_service import clasificar_calidad_aire_mp25  # noqa: E402

DEFAULT_DATASET_PATH = ROOT_DIR / "data" / "processed" / "dataset_modelado.csv"
DEFAULT_MODEL_PATH = ROOT_DIR / "models" / "regression" / "modelo_mp25_24h.joblib"
DEFAULT_METRICS_PATH = ROOT_DIR / "models" / "regression" / "metricas_regresion.json"
DEFAULT_PREDICTIONS_PATH = ROOT_DIR / "data" / "processed" / "predicciones_mp25_24h.csv"
LEGACY_MODEL_PATH = ROOT_DIR / "models" / "modelo_mp25_24h.joblib"
LEGACY_METRICS_PATH = ROOT_DIR / "models" / "metricas_regresion.json"

TARGET_HORIZON_HOURS = 24
SAMPLING_FREQUENCY_HOURS = 6
TARGET_SHIFT_STEPS = TARGET_HORIZON_HOURS // SAMPLING_FREQUENCY_HOURS
TRAIN_FRACTION = 0.8
TARGET_COLUMN = "mp25_24h"
LEGACY_TARGET_COLUMN = "mp25_24h_futuro"
DEFAULT_TIME_SERIES_SPLITS = 3

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
    "lag_3",
    "delta_mp25",
    "mp25_promedio_movil_3",
    "rolling_mean_6",
    "rolling_mean_12",
    "direccion_viento_sin",
    "direccion_viento_cos",
]

CATEGORICAL_FEATURES = [
    "tipo_sensor",
    "comuna",
    "region",
    "estacion_del_ano",
]

PREDICCIONES_COLUMNS = [
    "tipo_registro",
    "fecha_hora_base",
    "fecha_hora_objetivo",
    "fecha_hora",
    "codigo_estacion",
    "comuna",
    "region",
    "tipo_sensor",
    "mp25_actual",
    "mp25_real",
    "mp25_real_24h",
    "mp25_predicho",
    "mp25_predicho_24h",
    "error",
    "error_absoluto",
    "categoria_alerta",
    "categoria_predicha",
    "categoria_alerta_predicha",
    "mensaje_ciudadano",
    "color_referencial",
]

MOJIBAKE_MARKERS = ("\u00c3", "\u00c2", "\u00e2")
DEFAULT_CONTEXT_VALUES = {
    "indice_vulnerabilidad_respiratoria": 50.0,
    "emision_maxima_permitida": 200.0,
}
SEASON_BY_MONTH = {
    12: "verano",
    1: "verano",
    2: "verano",
    3: "otono",
    4: "otono",
    5: "otono",
    6: "invierno",
    7: "invierno",
    8: "invierno",
    9: "primavera",
    10: "primavera",
    11: "primavera",
}


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


def _resolver_ruta_lectura(path: str | Path, fallback: str | Path | None = None) -> Path:
    ruta = Path(path)
    if ruta.exists():
        return ruta

    if fallback is not None:
        ruta_fallback = Path(fallback)
        if ruta_fallback.exists():
            return ruta_fallback

    return ruta


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


def inferir_tipo_sensor(df: pd.DataFrame) -> pd.Series:
    """Infer sensor type when the dry-run dataset does not include it."""
    fuente = df.get("fuente_dato", pd.Series(index=df.index, dtype="object")).fillna("")
    codigo = df.get("codigo_estacion", pd.Series(index=df.index, dtype="object")).fillna("")

    fuente = fuente.astype(str).str.lower()
    codigo = codigo.astype(str).str.upper()

    tipo_sensor = pd.Series("sensor_desconocido", index=df.index, dtype="object")
    mascara_oficial = (
        fuente.isin(["oficial", "publico_oficial"])
        | codigo.str.contains("-OF-")
        | codigo.str.startswith("OF-")
    )
    mascara_ong = (
        fuente.isin(["comunitario", "sensor_comunitario_ong", "ong"])
        | codigo.str.contains("ONG")
    )

    tipo_sensor.loc[mascara_oficial] = "publico_oficial"
    tipo_sensor.loc[mascara_ong] = "sensor_comunitario_ong"
    return tipo_sensor


def completar_columnas_requeridas(df: pd.DataFrame) -> pd.DataFrame:
    """Complete optional context columns so regression also works after dry-run ETL."""
    dataset = df.copy()

    if "tipo_sensor" not in dataset.columns:
        dataset["tipo_sensor"] = inferir_tipo_sensor(dataset)
    else:
        dataset["tipo_sensor"] = dataset["tipo_sensor"].fillna(inferir_tipo_sensor(dataset))

    for columna, valor_default in DEFAULT_CONTEXT_VALUES.items():
        if columna not in dataset.columns:
            dataset[columna] = valor_default
        else:
            dataset[columna] = pd.to_numeric(dataset[columna], errors="coerce").fillna(valor_default)

    return dataset


def obtener_estacion_del_ano(fechas: pd.Series) -> pd.Series:
    """Map each timestamp month to a season in the southern hemisphere."""
    meses = pd.to_datetime(fechas, errors="coerce").dt.month
    return meses.map(SEASON_BY_MONTH).fillna("desconocida")


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
    df = completar_columnas_requeridas(df)
    validar_dataset_modelado(df)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    if df["fecha_hora"].isna().any():
        raise ValueError("El dataset contiene fechas invalidas en fecha_hora.")
    return df


def cargar_dataset(path: str | Path = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    """Public alias used by notebooks and demos."""
    return cargar_dataset_modelado(path)


def _ordenar_dataset_temporal(df: pd.DataFrame) -> pd.DataFrame:
    dataset = df.copy()
    dataset["fecha_hora"] = pd.to_datetime(dataset["fecha_hora"], errors="coerce")
    if dataset["fecha_hora"].isna().any():
        raise ValueError("El dataset contiene fechas invalidas en fecha_hora.")
    return dataset.sort_values(["codigo_estacion", "fecha_hora"]).reset_index(drop=True)


def crear_variable_objetivo(
    df: pd.DataFrame,
    target_shift_steps: int = TARGET_SHIFT_STEPS,
) -> pd.DataFrame:
    """Create the 24h-ahead regression target without leaking future rows."""
    dataset = _ordenar_dataset_temporal(df)

    grupo_estacion = dataset.groupby("codigo_estacion", group_keys=False, sort=False)
    dataset["mp25_24h_estacion"] = grupo_estacion["mp25"].shift(-target_shift_steps)

    serie_comuna = (
        dataset.groupby(["comuna", "fecha_hora"], as_index=False)["mp25"]
        .mean()
        .sort_values(["comuna", "fecha_hora"])
    )
    serie_comuna["mp25_24h_comuna"] = (
        serie_comuna.groupby("comuna", sort=False)["mp25"].shift(-target_shift_steps)
    )
    dataset = dataset.merge(
        serie_comuna[["comuna", "fecha_hora", "mp25_24h_comuna"]],
        on=["comuna", "fecha_hora"],
        how="left",
    )
    dataset[TARGET_COLUMN] = dataset["mp25_24h_estacion"].fillna(dataset["mp25_24h_comuna"])
    dataset[LEGACY_TARGET_COLUMN] = dataset[TARGET_COLUMN]
    dataset["fecha_hora_objetivo"] = dataset["fecha_hora"] + pd.Timedelta(hours=TARGET_HORIZON_HOURS)
    return dataset


def ingenieria_caracteristicas(df: pd.DataFrame) -> pd.DataFrame:
    """Add temporal, historical, and circular-wind features to the dataset."""
    dataset = _ordenar_dataset_temporal(df)

    dataset["hora"] = dataset["fecha_hora"].dt.hour
    dataset["dia"] = dataset["fecha_hora"].dt.day
    dataset["mes"] = dataset["fecha_hora"].dt.month
    dataset["dia_semana"] = dataset["fecha_hora"].dt.dayofweek
    dataset["estacion_del_ano"] = obtener_estacion_del_ano(dataset["fecha_hora"])

    angulo = np.deg2rad(pd.to_numeric(dataset["direccion_viento_grados"], errors="coerce"))
    dataset["direccion_viento_sin"] = np.sin(angulo)
    dataset["direccion_viento_cos"] = np.cos(angulo)

    grupo_estacion = dataset.groupby("codigo_estacion", group_keys=False, sort=False)
    dataset["lag_1"] = grupo_estacion["mp25"].shift(1)
    dataset["lag_2"] = grupo_estacion["mp25"].shift(2)
    dataset["lag_3"] = grupo_estacion["mp25"].shift(3)
    dataset["delta_mp25"] = dataset["mp25"] - dataset["lag_1"]
    dataset["mp25_promedio_movil_3"] = grupo_estacion["mp25"].transform(
        lambda serie: serie.shift(1).rolling(window=3, min_periods=1).mean()
    )
    dataset["rolling_mean_6"] = grupo_estacion["mp25"].transform(
        lambda serie: serie.shift(1).rolling(window=6, min_periods=1).mean()
    )
    dataset["rolling_mean_12"] = grupo_estacion["mp25"].transform(
        lambda serie: serie.shift(1).rolling(window=12, min_periods=1).mean()
    )
    return dataset


def preparar_dataset_regresion(
    df: pd.DataFrame,
    target_shift_steps: int = TARGET_SHIFT_STEPS,
) -> pd.DataFrame:
    """Create temporal and historical features without using future information."""
    dataset = crear_variable_objetivo(df, target_shift_steps=target_shift_steps)
    return ingenieria_caracteristicas(dataset)


def filtrar_dataset_entrenamiento(df: pd.DataFrame) -> pd.DataFrame:
    """Keep rows that have a known target for supervised learning."""
    dataset = df.loc[df[TARGET_COLUMN].notna()].copy()
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
    y_train = train_df[TARGET_COLUMN]
    x_test = test_df[columnas_features]
    y_test = test_df[TARGET_COLUMN]

    resultados: dict[str, ResultadoEntrenamiento] = {}
    for nombre, pipeline in modelos.items():
        pipeline.fit(x_train, y_train)
        predicciones = pipeline.predict(x_test)
        resultados[nombre] = ResultadoEntrenamiento(
            nombre_modelo=nombre,
            pipeline=pipeline,
            metricas=evaluar_modelo(y_test, predicciones),
            predicciones_test=predicciones,
        )
    return resultados


def evaluar_modelo(y_real: pd.Series | np.ndarray, y_predicho: pd.Series | np.ndarray) -> dict[str, float]:
    """Compute the main regression metrics used in reports and comparisons."""
    return {
        "mae": float(mean_absolute_error(y_real, y_predicho)),
        "rmse": float(np.sqrt(mean_squared_error(y_real, y_predicho))),
        "r2": float(r2_score(y_real, y_predicho)),
    }


def evaluar_modelos_time_series_cv(
    train_df: pd.DataFrame,
    random_state: int = 42,
    n_splits: int = DEFAULT_TIME_SERIES_SPLITS,
) -> dict[str, dict[str, Any]]:
    """Optionally evaluate candidate models with TimeSeriesSplit on the training window."""
    if len(train_df) < (n_splits + 1) * 2:
        return {}

    columnas_features = obtener_columnas_features()
    x_train = train_df[columnas_features].reset_index(drop=True)
    y_train = train_df[TARGET_COLUMN].reset_index(drop=True)

    splitter = TimeSeriesSplit(n_splits=n_splits)
    modelos = construir_modelos(random_state=random_state)
    resumen_cv: dict[str, dict[str, Any]] = {}

    for nombre, pipeline in modelos.items():
        metricas_folds: list[dict[str, float]] = []

        for fold, (train_idx, valid_idx) in enumerate(splitter.split(x_train), start=1):
            modelo_fold = clone(pipeline)
            modelo_fold.fit(x_train.iloc[train_idx], y_train.iloc[train_idx])
            predicciones = modelo_fold.predict(x_train.iloc[valid_idx])
            y_valid = y_train.iloc[valid_idx]
            metricas_folds.append(
                {
                    "fold": float(fold),
                    "mae": float(mean_absolute_error(y_valid, predicciones)),
                    "rmse": float(np.sqrt(mean_squared_error(y_valid, predicciones))),
                    "r2": float(r2_score(y_valid, predicciones)),
                }
            )

        resumen_cv[nombre] = {
            "n_splits": n_splits,
            "mean_mae": float(np.mean([fold["mae"] for fold in metricas_folds])),
            "mean_rmse": float(np.mean([fold["rmse"] for fold in metricas_folds])),
            "mean_r2": float(np.mean([fold["r2"] for fold in metricas_folds])),
            "folds": metricas_folds,
        }

    return resumen_cv


def seleccionar_mejor_modelo(metricas_por_modelo: dict[str, dict[str, float]]) -> str:
    """Pick the winner using the lowest RMSE."""
    if not metricas_por_modelo:
        raise ValueError("No hay metricas para seleccionar el mejor modelo.")
    return min(metricas_por_modelo, key=lambda nombre: metricas_por_modelo[nombre]["rmse"])


def predecir(modelo: Pipeline, df: pd.DataFrame) -> np.ndarray:
    """Generate predictions from a fitted pipeline using the standard feature set."""
    columnas_features = obtener_columnas_features()
    if set(columnas_features).issubset(df.columns):
        return modelo.predict(df[columnas_features])
    return modelo.predict(df)


def _aplicar_clasificacion_predicha(predicciones: pd.Series) -> pd.DataFrame:
    clasificaciones = predicciones.apply(lambda valor: clasificar_mp25(float(valor)))
    return pd.DataFrame(clasificaciones.tolist(), index=predicciones.index)


def _enriquecer_exporte_predicciones(df: pd.DataFrame) -> pd.DataFrame:
    exportable = df.copy()
    exportable["fecha_hora"] = exportable["fecha_hora_objetivo"]
    exportable["mp25_real_24h"] = exportable["mp25_real"]
    exportable["mp25_predicho_24h"] = exportable["mp25_predicho"]
    exportable["error"] = exportable["mp25_real_24h"] - exportable["mp25_predicho_24h"]
    exportable["error_absoluto"] = (
        exportable["error"]
    ).abs()
    exportable["categoria_alerta"] = exportable["categoria_predicha"]
    exportable["categoria_alerta_predicha"] = exportable["categoria_predicha"]
    return exportable[PREDICCIONES_COLUMNS]


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
            TARGET_COLUMN,
        ]
    ].copy()
    base = base.rename(
        columns={
            "fecha_hora": "fecha_hora_base",
            "mp25": "mp25_actual",
            TARGET_COLUMN: "mp25_real",
        }
    )
    base["tipo_registro"] = "evaluacion"
    base["mp25_predicho"] = predicciones
    clasificacion = _aplicar_clasificacion_predicha(base["mp25_predicho"])
    base["categoria_predicha"] = clasificacion["categoria"]
    base["mensaje_ciudadano"] = clasificacion["mensaje_ciudadano"]
    base["color_referencial"] = clasificacion["color_referencial"]
    return _enriquecer_exporte_predicciones(base)


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

    predicciones = predecir(modelo, ultimas_filas[columnas_features])
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
    return _enriquecer_exporte_predicciones(pronosticos)


def guardar_modelo(modelo: Pipeline, path: str | Path = DEFAULT_MODEL_PATH) -> Path:
    """Persist the fitted pipeline."""
    output_path = Path(path)
    _asegurar_directorio(output_path)
    joblib.dump(modelo, output_path)
    return output_path


def cargar_modelo(path: str | Path = DEFAULT_MODEL_PATH) -> Pipeline:
    """Load the fitted regression pipeline."""
    return joblib.load(_resolver_ruta_lectura(path, LEGACY_MODEL_PATH))


def guardar_metricas(metricas: dict[str, Any], path: str | Path = DEFAULT_METRICS_PATH) -> Path:
    """Write the training metadata and scores as JSON."""
    output_path = Path(path)
    _asegurar_directorio(output_path)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(metricas, file, ensure_ascii=False, indent=2)
    return output_path


def cargar_metricas(path: str | Path = DEFAULT_METRICS_PATH) -> dict[str, Any]:
    """Load the saved metrics JSON."""
    with _resolver_ruta_lectura(path, LEGACY_METRICS_PATH).open(encoding="utf-8") as file:
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
    metricas_time_series_cv = evaluar_modelos_time_series_cv(train_df)
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
        "features_used": obtener_columnas_features(),
        "models": metricas_por_modelo,
    }
    if metricas_time_series_cv:
        metricas["time_series_cv"] = metricas_time_series_cv

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
