"""Professional Streamlit dashboard for the air quality monitoring project."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
CLUSTER_METRICS_PATH = ROOT_DIR / "models" / "clustering" / "metricas_clustering.json"

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.clustering import DEFAULT_CLUSTERS_PATH, DEFAULT_SUMMARY_PATH  # noqa: E402
from src.regression import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_METRICS_PATH,
    DEFAULT_MODEL_PATH,
    DEFAULT_PREDICTIONS_PATH,
    cargar_modelo,
    clasificar_mp25,
    obtener_importancia_variables,
)


st.set_page_config(
    page_title="Calidad del Aire Centro-Sur",
    page_icon="AQ",
    layout="wide",
)


VIEW_OPTIONS = {
    "Vista Ejecutiva / Municipal": "executive",
    "Vista Tecnica / Analitica": "technical",
    "Vista Ciudadana / Vecinos": "citizen",
}

ALERT_PRIORITY = {
    "Buena": 0,
    "Regular": 1,
    "Alerta": 2,
    "Preemergencia": 3,
    "Emergencia": 4,
}

STATUS_BY_CATEGORY = {
    "Buena": "success",
    "Regular": "info",
    "Alerta": "warning",
    "Preemergencia": "error",
    "Emergencia": "error",
}

MOJIBAKE_COLUMNS = [
    "comuna",
    "region",
    "tipo_sensor",
    "categoria_ica",
    "codigo_estacion",
    "nivel_riesgo",
    "categoria_alerta",
    "categoria_predicha",
    "categoria_alerta_predicha",
    "mensaje_ciudadano",
]

DATASET_MISSING_MESSAGE = (
    "No se encontro el dataset modelado. Ejecuta primero el ETL."
)
PREDICTIONS_MISSING_MESSAGE = (
    "No se encontro el archivo de predicciones. Ejecuta primero `python src/regression.py`."
)
CLUSTERS_MISSING_MESSAGE = (
    "No se encontro el archivo de clustering. Ejecuta primero el flujo de clustering."
)
SUMMARY_MISSING_MESSAGE = (
    "No se encontro el resumen de clusters. Ejecuta primero `python src/clustering.py`."
)
REGRESSION_METRICS_MISSING_MESSAGE = (
    "No se encontraron las metricas de regresion. Ejecuta primero `python src/regression.py`."
)
CLUSTER_METRICS_MISSING_MESSAGE = (
    "No se encontraron las metricas de clustering. Ejecuta primero `python src/clustering.py`."
)


def fix_mojibake(value: Any) -> Any:
    """Fix frequent UTF-8 text incorrectly decoded as latin-1."""
    if not isinstance(value, str):
        return value

    markers = ("Ã", "Â", "â")
    text = " ".join(value.split())
    if not text or not any(marker in text for marker in markers):
        return text

    try:
        return text.encode("latin-1").decode("utf-8")
    except UnicodeError:
        return text


def normalize_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize visible label columns for display."""
    normalized = df.copy()
    for column in MOJIBAKE_COLUMNS:
        if column in normalized.columns:
            normalized[column] = normalized[column].map(fix_mojibake)
    return normalized


def classify_alert(value: float) -> dict[str, str]:
    """Return the simplified alert category used across the dashboard."""
    return clasificar_mp25(float(value))


def build_citizen_outlook(value: float | None) -> str:
    """Generate a simple, non-technical citizen message from the predicted MP2.5."""
    if value is None or pd.isna(value):
        return "Todavia no hay un pronostico disponible para las proximas 24 horas."

    category = classify_alert(float(value))["categoria"]
    if category == "Buena":
        return (
            "La calidad del aire estimada para las proximas 24 horas se mantiene en niveles bajos de riesgo."
        )
    if category == "Regular":
        return (
            "Se espera un aumento moderado de MP2.5. Conviene monitorear la evolucion durante el dia."
        )
    if category == "Alerta":
        return (
            "El modelo estima un aumento relevante de MP2.5 para las proximas 24 horas."
        )
    if category == "Preemergencia":
        return (
            "El modelo estima niveles altos de MP2.5 para las proximas 24 horas. Esta comuna requiere atencion preventiva."
        )
    return (
        "Se proyectan niveles muy altos de MP2.5 para las proximas 24 horas. Esta comuna requiere atencion preventiva inmediata."
    )


def get_alert_column(df: pd.DataFrame) -> str | None:
    """Return the alert category column available in the dataframe."""
    for candidate in ("categoria_alerta_predicha", "categoria_alerta", "categoria_predicha"):
        if candidate in df.columns:
            return candidate
    return None


def ensure_prediction_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill expected columns so the dashboard can work with older exports."""
    predictions = df.copy()

    if "mp25_predicho_24h" not in predictions.columns and "mp25_predicho" in predictions.columns:
        predictions["mp25_predicho_24h"] = predictions["mp25_predicho"]
    if "mp25_real_24h" not in predictions.columns and "mp25_real" in predictions.columns:
        predictions["mp25_real_24h"] = predictions["mp25_real"]
    if "error" not in predictions.columns and {
        "mp25_real_24h",
        "mp25_predicho_24h",
    }.issubset(predictions.columns):
        predictions["error"] = predictions["mp25_real_24h"] - predictions["mp25_predicho_24h"]
    if "error_absoluto" not in predictions.columns and "error" in predictions.columns:
        predictions["error_absoluto"] = predictions["error"].abs()

    if "categoria_alerta_predicha" not in predictions.columns:
        prediction_value_column = None
        for candidate in ("mp25_predicho_24h", "mp25_predicho"):
            if candidate in predictions.columns:
                prediction_value_column = candidate
                break
        if prediction_value_column is not None:
            predictions["categoria_alerta_predicha"] = predictions[prediction_value_column].map(
                lambda value: classify_alert(float(value))["categoria"]
            )

    if "categoria_alerta" not in predictions.columns and "categoria_alerta_predicha" in predictions.columns:
        predictions["categoria_alerta"] = predictions["categoria_alerta_predicha"]

    if "mensaje_ciudadano" not in predictions.columns:
        predictions["mensaje_ciudadano"] = predictions.get("mp25_predicho_24h", pd.Series(index=predictions.index)).map(
            lambda value: classify_alert(float(value))["mensaje_ciudadano"] if pd.notna(value) else ""
        )

    return normalize_labels(predictions)


@st.cache_data(show_spinner=False)
def load_dataset(path: str) -> pd.DataFrame:
    """Load the main modeling dataset used as the dashboard backbone."""
    dataset = pd.read_csv(path)
    dataset = normalize_labels(dataset)
    if "fecha_hora" in dataset.columns:
        dataset["fecha_hora"] = pd.to_datetime(dataset["fecha_hora"], errors="coerce")
    return dataset


@st.cache_data(show_spinner=False)
def load_predictions(path: str) -> pd.DataFrame:
    """Load regression predictions and harmonize the expected columns."""
    predictions = pd.read_csv(path)
    predictions = ensure_prediction_columns(predictions)
    for column in ("fecha_hora_base", "fecha_hora_objetivo", "fecha_hora"):
        if column in predictions.columns:
            predictions[column] = pd.to_datetime(predictions[column], errors="coerce")
    return predictions


@st.cache_data(show_spinner=False)
def load_clusters(path: str) -> pd.DataFrame:
    """Load clustering assignments for each monitoring record."""
    clusters = pd.read_csv(path)
    clusters = normalize_labels(clusters)
    if "fecha_hora" in clusters.columns:
        clusters["fecha_hora"] = pd.to_datetime(clusters["fecha_hora"], errors="coerce")
    return clusters


@st.cache_data(show_spinner=False)
def load_cluster_summary(path: str) -> pd.DataFrame:
    """Load the aggregate cluster summary table."""
    summary = pd.read_csv(path)
    return normalize_labels(summary)


@st.cache_data(show_spinner=False)
def load_metrics(path: str) -> dict[str, Any]:
    """Load a JSON metrics artifact."""
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


@st.cache_resource(show_spinner=False)
def load_model(path: str):
    """Load the persisted regression model only when it exists."""
    return cargar_modelo(path)


def filter_data(
    df: pd.DataFrame | None,
    filters: dict[str, Any],
    *,
    date_column: str | None = None,
) -> pd.DataFrame:
    """Apply the global filters only when the corresponding columns exist."""
    if df is None:
        return pd.DataFrame()

    filtered = df.copy()
    if filtered.empty:
        return filtered

    if filters["regions"] and "region" in filtered.columns:
        filtered = filtered[filtered["region"].isin(filters["regions"])]
    if filters["communes"] and "comuna" in filtered.columns:
        filtered = filtered[filtered["comuna"].isin(filters["communes"])]
    if filters["sensor_types"] and "tipo_sensor" in filtered.columns:
        filtered = filtered[filtered["tipo_sensor"].isin(filters["sensor_types"])]
    if filters["risk_levels"] and "nivel_riesgo" in filtered.columns:
        filtered = filtered[filtered["nivel_riesgo"].isin(filters["risk_levels"])]

    alert_column = get_alert_column(filtered)
    if filters["alert_categories"] and alert_column is not None:
        filtered = filtered[filtered[alert_column].isin(filters["alert_categories"])]

    if date_column and date_column in filtered.columns:
        filtered = filtered[
            (filtered[date_column] >= filters["date_start"])
            & (filtered[date_column] <= filters["date_end"])
        ]

    return filtered


def build_cluster_summary_from_rows(clusters_df: pd.DataFrame) -> pd.DataFrame:
    """Build a summary table directly from row-level clustering output if needed."""
    if clusters_df.empty or "cluster" not in clusters_df.columns:
        return pd.DataFrame()

    summary = (
        clusters_df.groupby(["cluster", "nivel_riesgo"], as_index=False)
        .agg(
            cantidad_registros=("codigo_estacion", "size"),
            mp25=("mp25", "mean"),
            mp10=("mp10", "mean"),
            so2=("so2", "mean"),
            no2=("no2", "mean"),
            humedad=("humedad", "mean"),
            indice_vulnerabilidad_respiratoria=("indice_vulnerabilidad_respiratoria", "mean"),
            emision_maxima_permitida=("emision_maxima_permitida", "mean"),
            velocidad_viento=("velocidad_viento", "mean"),
        )
        .sort_values("cantidad_registros", ascending=False)
    )
    return summary


def render_sidebar(
    dataset: pd.DataFrame,
    predictions: pd.DataFrame | None,
    clusters: pd.DataFrame | None,
) -> dict[str, Any]:
    """Render the global filters and audience selector."""
    st.sidebar.header("Filtros globales")

    frames = [frame for frame in (dataset, predictions, clusters) if frame is not None and not frame.empty]

    def collect_options(column: str) -> list[str]:
        values: set[str] = set()
        for frame in frames:
            if column in frame.columns:
                values.update(
                    {
                        str(value)
                        for value in frame[column].dropna().tolist()
                        if str(value).strip()
                    }
                )
        return sorted(values)

    regions = collect_options("region")
    communes = collect_options("comuna")
    sensor_types = collect_options("tipo_sensor")
    risk_levels = collect_options("nivel_riesgo")
    alert_categories = sorted(
        {
            str(value)
            for frame in frames
            for column in ("categoria_alerta_predicha", "categoria_alerta", "categoria_predicha")
            if column in frame.columns
            for value in frame[column].dropna().tolist()
            if str(value).strip()
        },
        key=lambda category: ALERT_PRIORITY.get(category, 999),
    )

    min_date = dataset["fecha_hora"].min().date()
    max_date = dataset["fecha_hora"].max().date()

    selected_view = st.sidebar.radio("Vista", list(VIEW_OPTIONS.keys()), index=0)
    selected_regions = st.sidebar.multiselect("Region", regions)
    selected_communes = st.sidebar.multiselect("Comuna", communes)
    selected_sensor_types = st.sidebar.multiselect("Tipo de sensor", sensor_types)
    date_range = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    selected_risk_levels: list[str] = []
    if risk_levels:
        selected_risk_levels = st.sidebar.multiselect("Nivel de riesgo", risk_levels)

    selected_alert_categories: list[str] = []
    if alert_categories:
        selected_alert_categories = st.sidebar.multiselect("Categoria de alerta", alert_categories)

    st.sidebar.caption(
        "Los filtros se aplican solo cuando la columna correspondiente existe en el archivo cargado."
    )

    return {
        "view": VIEW_OPTIONS[selected_view],
        "regions": selected_regions,
        "communes": selected_communes,
        "sensor_types": selected_sensor_types,
        "risk_levels": selected_risk_levels,
        "alert_categories": selected_alert_categories,
        "date_start": pd.Timestamp(date_range[0]),
        "date_end": pd.Timestamp(date_range[-1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1),
    }


def render_missing_artifact_warnings(missing_messages: list[str]) -> None:
    """Show clear warnings for optional artifacts that are not available."""
    if not missing_messages:
        return

    st.warning("Algunos artefactos opcionales no estan disponibles todavia:")
    for message in missing_messages:
        st.markdown(f"- {message}")


def render_executive_view(dataset: pd.DataFrame, predictions: pd.DataFrame | None) -> None:
    """Render the executive / municipal view."""
    st.subheader("Vista Ejecutiva / Municipal")
    st.caption(
        "Esta vista resume el estado general del monitoreo ambiental y ayuda a priorizar comunas con mayor necesidad de atencion preventiva."
    )

    if dataset.empty:
        st.info("No hay datos historicos para los filtros actuales.")
        return

    forecast = pd.DataFrame()
    if predictions is not None and not predictions.empty:
        forecast = predictions.loc[predictions["tipo_registro"] == "pronostico_24h"].copy()

    historical_alert_mask = dataset.get("categoria_ica", pd.Series(index=dataset.index)).isin(
        ["Alerta", "Preemergencia", "Emergencia"]
    )
    critical_commune = (
        dataset.groupby("comuna", as_index=False)["mp25"]
        .mean()
        .sort_values("mp25", ascending=False)
        .iloc[0]
    )

    alert_percentage = float(historical_alert_mask.mean() * 100) if len(dataset) else 0.0
    forecast_average = float(forecast["mp25_predicho_24h"].mean()) if not forecast.empty else float("nan")
    forecast_alerts = 0
    if not forecast.empty:
        alert_column = get_alert_column(forecast)
        if alert_column is not None:
            forecast_alerts = int(
                forecast[alert_column].isin(["Alerta", "Preemergencia", "Emergencia"]).sum()
            )

    top_row = st.columns(3)
    top_row[0].metric("MP2.5 promedio", f"{dataset['mp25'].mean():.2f}")
    top_row[1].metric("MP2.5 maximo", f"{dataset['mp25'].max():.2f}")
    top_row[2].metric("Total de mediciones", f"{len(dataset):,}")

    bottom_row = st.columns(3)
    bottom_row[0].metric("Comuna mas critica", critical_commune["comuna"])
    bottom_row[1].metric("% registros en alerta o riesgo", f"{alert_percentage:.1f}%")
    bottom_row[2].metric(
        "Pronostico promedio 24h",
        "N/D" if pd.isna(forecast_average) else f"{forecast_average:.2f}",
        delta=f"{forecast_alerts} alertas pronosticadas" if forecast_alerts else None,
    )

    ranking_source = forecast if not forecast.empty else dataset
    ranking_column = "mp25_predicho_24h" if not forecast.empty else "mp25"
    ranking = (
        ranking_source.groupby(["comuna", "region"], as_index=False)[ranking_column]
        .mean()
        .sort_values(ranking_column, ascending=False)
        .head(12)
    )

    trend = (
        dataset.assign(fecha=dataset["fecha_hora"].dt.date)
        .groupby("fecha", as_index=False)["mp25"]
        .mean()
        .sort_values("fecha")
    )

    left_column, right_column = st.columns([1, 1])
    with left_column:
        ranking_chart = px.bar(
            ranking.sort_values(ranking_column, ascending=True),
            x=ranking_column,
            y="comuna",
            color="region",
            orientation="h",
            title="Ranking de comunas por MP2.5",
            labels={ranking_column: "MP2.5 promedio", "comuna": "Comuna"},
        )
        st.plotly_chart(ranking_chart, use_container_width=True)

    with right_column:
        trend_chart = px.line(
            trend,
            x="fecha",
            y="mp25",
            markers=True,
            title="Evolucion temporal de MP2.5",
            labels={"fecha": "Fecha", "mp25": "MP2.5 promedio"},
        )
        st.plotly_chart(trend_chart, use_container_width=True)

    if not forecast.empty:
        alert_column = get_alert_column(forecast)
        if alert_column is not None:
            alert_counts = (
                forecast.groupby(alert_column, as_index=False)
                .size()
                .rename(columns={"size": "cantidad"})
            )
            alert_counts[alert_column] = pd.Categorical(
                alert_counts[alert_column],
                categories=list(ALERT_PRIORITY.keys()),
                ordered=True,
            )
            alert_counts = alert_counts.sort_values(alert_column)

            alerts_chart = px.bar(
                alert_counts,
                x=alert_column,
                y="cantidad",
                color=alert_column,
                title="Resumen de alertas predictivas",
                labels={alert_column: "Categoria", "cantidad": "Pronosticos"},
            )
            st.plotly_chart(alerts_chart, use_container_width=True)

            alert_summary = (
                forecast.groupby(["comuna", "region", alert_column], as_index=False)
                .agg(
                    mp25_predicho_24h=("mp25_predicho_24h", "mean"),
                    estaciones=("codigo_estacion", "nunique"),
                )
                .sort_values("mp25_predicho_24h", ascending=False)
                .head(12)
            )
            st.dataframe(alert_summary, use_container_width=True, hide_index=True)
    else:
        st.info("Todavia no hay pronosticos disponibles para mostrar alertas predictivas.")


def render_regression_metrics(metrics: dict[str, Any] | None, evaluation: pd.DataFrame) -> None:
    """Render the key regression metrics in the technical view."""
    if not metrics or "models" not in metrics:
        st.info(REGRESSION_METRICS_MISSING_MESSAGE)
        return

    best_model = metrics.get("best_model")
    best_values = metrics["models"].get(best_model, {}) if best_model else {}
    mean_absolute_error = best_values.get("mae")
    root_mean_squared_error = best_values.get("rmse")
    r_squared = best_values.get("r2")
    average_abs_error = (
        float(evaluation["error_absoluto"].mean()) if not evaluation.empty and "error_absoluto" in evaluation.columns else float("nan")
    )

    metric_columns = st.columns(4)
    metric_columns[0].metric("Modelo ganador", best_model or "N/D")
    metric_columns[1].metric("MAE", "N/D" if mean_absolute_error is None else f"{mean_absolute_error:.2f}")
    metric_columns[2].metric("RMSE", "N/D" if root_mean_squared_error is None else f"{root_mean_squared_error:.2f}")
    metric_columns[3].metric(
        "R2 / Error abs. promedio",
        "N/D" if r_squared is None else f"{r_squared:.3f}",
        delta=None if pd.isna(average_abs_error) else f"Error abs. {average_abs_error:.2f}",
    )

    comparison_table = (
        pd.DataFrame(metrics["models"]).T.reset_index().rename(columns={"index": "modelo"})
    )
    st.dataframe(comparison_table, use_container_width=True, hide_index=True)


def render_clustering_metrics(cluster_metrics: dict[str, Any] | None) -> None:
    """Render clustering metadata and aggregate quality metrics."""
    if not cluster_metrics:
        st.info(CLUSTER_METRICS_MISSING_MESSAGE)
        return

    metric_columns = st.columns(4)
    metric_columns[0].metric("Algoritmo", cluster_metrics.get("algoritmo", "N/D"))
    metric_columns[1].metric("Clusters", str(cluster_metrics.get("n_clusters", "N/D")))
    metric_columns[2].metric("Silhouette", f"{cluster_metrics.get('silhouette', float('nan')):.3f}")
    metric_columns[3].metric("Inercia", f"{cluster_metrics.get('inercia', float('nan')):.2f}")

    evaluation_k = pd.DataFrame(cluster_metrics.get("evaluacion_k", []))
    if not evaluation_k.empty:
        st.dataframe(evaluation_k, use_container_width=True, hide_index=True)


def render_technical_view(
    predictions: pd.DataFrame | None,
    regression_metrics: dict[str, Any] | None,
    importance_df: pd.DataFrame,
    clusters: pd.DataFrame | None,
    cluster_summary: pd.DataFrame,
    cluster_metrics: dict[str, Any] | None,
) -> None:
    """Render the technical / analytics view."""
    st.subheader("Vista Tecnica / Analitica")
    st.caption(
        "Esta vista permite evaluar el comportamiento del modelo predictivo y la segmentacion de riesgo ambiental generada por K-Means."
    )

    evaluation = pd.DataFrame()
    if predictions is not None and not predictions.empty:
        evaluation = predictions.loc[predictions["tipo_registro"] == "evaluacion"].copy()

    render_regression_metrics(regression_metrics, evaluation)

    left_column, right_column = st.columns([1.25, 1])
    with left_column:
        if evaluation.empty:
            st.info(PREDICTIONS_MISSING_MESSAGE)
        else:
            scatter = px.scatter(
                evaluation,
                x="mp25_real_24h",
                y="mp25_predicho_24h",
                color="comuna",
                hover_data=["codigo_estacion", "fecha_hora_base", "fecha_hora_objetivo"],
                title="Comparacion MP2.5 real vs predicho",
                labels={
                    "mp25_real_24h": "MP2.5 real 24h",
                    "mp25_predicho_24h": "MP2.5 predicho 24h",
                },
            )
            min_value = min(evaluation["mp25_real_24h"].min(), evaluation["mp25_predicho_24h"].min())
            max_value = max(evaluation["mp25_real_24h"].max(), evaluation["mp25_predicho_24h"].max())
            scatter.add_shape(
                type="line",
                x0=min_value,
                y0=min_value,
                x1=max_value,
                y1=max_value,
                line={"dash": "dash"},
            )
            st.plotly_chart(scatter, use_container_width=True)

    with right_column:
        if evaluation.empty or "error_absoluto" not in evaluation.columns:
            st.info("No hay suficientes datos para el histograma de errores.")
        else:
            error_histogram = px.histogram(
                evaluation,
                x="error_absoluto",
                nbins=30,
                title="Distribucion del error absoluto",
                labels={"error_absoluto": "Error absoluto"},
            )
            st.plotly_chart(error_histogram, use_container_width=True)

    lower_left, lower_right = st.columns([1, 1])
    with lower_left:
        if importance_df.empty:
            st.info("La importancia de variables solo se muestra cuando existe el modelo serializado.")
        else:
            importance_chart = px.bar(
                importance_df.sort_values("importance"),
                x="importance",
                y="feature",
                orientation="h",
                title="Importancia de variables",
                labels={"importance": "Importancia", "feature": "Variable"},
            )
            st.plotly_chart(importance_chart, use_container_width=True)

    with lower_right:
        render_clustering_metrics(cluster_metrics)

    if clusters is not None and not clusters.empty and "nivel_riesgo" in clusters.columns:
        distribution = (
            clusters.groupby("nivel_riesgo", as_index=False)
            .size()
            .rename(columns={"size": "cantidad"})
        )
        distribution["nivel_riesgo"] = pd.Categorical(
            distribution["nivel_riesgo"],
            categories=["Bajo riesgo", "Riesgo moderado", "Riesgo critico"],
            ordered=True,
        )
        distribution = distribution.sort_values("nivel_riesgo")

        distribution_chart = px.bar(
            distribution,
            x="nivel_riesgo",
            y="cantidad",
            color="nivel_riesgo",
            title="Distribucion de clusters de riesgo",
            labels={"nivel_riesgo": "Nivel de riesgo", "cantidad": "Registros"},
        )
        st.plotly_chart(distribution_chart, use_container_width=True)
    else:
        st.info(CLUSTERS_MISSING_MESSAGE)

    if not cluster_summary.empty:
        st.dataframe(cluster_summary, use_container_width=True, hide_index=True)

    if not evaluation.empty:
        columns_to_show = [
            column
            for column in [
                "fecha_hora_base",
                "fecha_hora_objetivo",
                "codigo_estacion",
                "comuna",
                "tipo_sensor",
                "mp25_actual",
                "mp25_real_24h",
                "mp25_predicho_24h",
                "error",
                "error_absoluto",
                "categoria_alerta_predicha",
            ]
            if column in evaluation.columns
        ]
        st.dataframe(
            evaluation[columns_to_show].sort_values("fecha_hora_base", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


def render_status_box(category: str, message: str) -> None:
    """Render a Streamlit callout matched to the citizen message severity."""
    status = STATUS_BY_CATEGORY.get(category, "info")
    if status == "success":
        st.success(message)
    elif status == "warning":
        st.warning(message)
    elif status == "error":
        st.error(message)
    else:
        st.info(message)


def render_citizen_view(dataset: pd.DataFrame, predictions: pd.DataFrame | None) -> None:
    """Render the citizen / neighborhood view."""
    st.subheader("Vista Ciudadana / Vecinos")
    st.caption(
        "Esta vista comunica el estado actual y el pronostico de calidad del aire con lenguaje simple y orientado a prevencion."
    )

    if dataset.empty:
        st.info("No hay datos disponibles para las comunas seleccionadas.")
        return

    available_communes = sorted(dataset["comuna"].dropna().unique().tolist())
    selected_commune = st.selectbox("Selecciona una comuna", available_communes)

    commune_history = dataset.loc[dataset["comuna"] == selected_commune].sort_values("fecha_hora")
    latest_row = commune_history.tail(1)
    current_mp25 = float(latest_row["mp25"].iloc[0]) if not latest_row.empty else float("nan")
    current_category = classify_alert(current_mp25)["categoria"] if pd.notna(current_mp25) else "N/D"

    commune_forecast = pd.DataFrame()
    if predictions is not None and not predictions.empty:
        commune_forecast = predictions.loc[
            (predictions["tipo_registro"] == "pronostico_24h") & (predictions["comuna"] == selected_commune)
        ].copy()

    forecast_value: float | None = None
    forecast_category = current_category
    forecast_target = None
    stations_considered = 0

    if not commune_forecast.empty:
        latest_target = commune_forecast["fecha_hora_objetivo"].max()
        latest_forecast_rows = commune_forecast.loc[
            commune_forecast["fecha_hora_objetivo"] == latest_target
        ]
        forecast_value = float(latest_forecast_rows["mp25_predicho_24h"].mean())
        forecast_category = classify_alert(forecast_value)["categoria"]
        forecast_target = latest_target
        stations_considered = int(latest_forecast_rows["codigo_estacion"].nunique())

    citizen_message = build_citizen_outlook(forecast_value)

    metric_columns = st.columns(4)
    metric_columns[0].metric("Estado actual", current_category)
    metric_columns[1].metric("MP2.5 actual", "N/D" if pd.isna(current_mp25) else f"{current_mp25:.2f}")
    metric_columns[2].metric(
        "MP2.5 esperado 24h",
        "N/D" if forecast_value is None else f"{forecast_value:.2f}",
    )
    metric_columns[3].metric("Estaciones consideradas", stations_considered)

    render_status_box(forecast_category, citizen_message)

    st.markdown(
        f"""
        **Comuna:** {selected_commune}  
        **Fecha ultima observacion:** {latest_row['fecha_hora'].iloc[0] if not latest_row.empty else 'N/D'}  
        **Fecha objetivo del pronostico:** {forecast_target if forecast_target is not None else 'N/D'}  
        **Recomendacion general:** Mantener seguimiento del estado del aire y priorizar prevencion cuando el pronostico sube de categoria.
        """
    )

    recent_history = commune_history.tail(20).copy()
    if not recent_history.empty:
        history_chart = px.line(
            recent_history,
            x="fecha_hora",
            y="mp25",
            markers=True,
            title=f"Evolucion reciente de MP2.5 en {selected_commune}",
            labels={"fecha_hora": "Fecha y hora", "mp25": "MP2.5"},
        )
        st.plotly_chart(history_chart, use_container_width=True)

    if not commune_forecast.empty:
        detail_columns = [
            column
            for column in [
                "codigo_estacion",
                "tipo_sensor",
                "fecha_hora_base",
                "fecha_hora_objetivo",
                "mp25_actual",
                "mp25_predicho_24h",
                "categoria_alerta_predicha",
                "mensaje_ciudadano",
            ]
            if column in commune_forecast.columns
        ]
        st.dataframe(
            commune_forecast[detail_columns].sort_values("mp25_predicho_24h", ascending=False),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Todavia no hay pronosticos disponibles para esta comuna.")


def render_footer(
    *,
    dataset: pd.DataFrame,
    predictions: pd.DataFrame | None,
    clusters: pd.DataFrame | None,
) -> None:
    """Render the dashboard footer with provenance and coverage information."""
    sources = ["dataset_modelado.csv"]
    if predictions is not None and not predictions.empty:
        sources.append("predicciones_mp25_24h.csv")
    if clusters is not None and not clusters.empty:
        sources.append("clusters_riesgo_ambiental.csv")

    st.markdown("---")
    st.caption(
        "Dashboard conectado a la salida del ETL, clustering y regresion. "
        f"Fuentes activas: {', '.join(sources)}. "
        f"Ventana historica cargada: {dataset['fecha_hora'].min()} a {dataset['fecha_hora'].max()}."
    )


def main() -> None:
    """Run the Streamlit dashboard."""
    st.title("Monitoreo de Calidad del Aire Centro-Sur")
    st.write(
        "Panel interactivo para explorar el estado historico del aire, perfiles de riesgo ambiental y pronosticos de MP2.5 a 24 horas."
    )

    if not Path(DEFAULT_DATASET_PATH).exists():
        st.error(DATASET_MISSING_MESSAGE)
        st.stop()

    dataset = load_dataset(str(DEFAULT_DATASET_PATH))

    missing_messages: list[str] = []
    predictions = None
    if Path(DEFAULT_PREDICTIONS_PATH).exists():
        predictions = load_predictions(str(DEFAULT_PREDICTIONS_PATH))
    else:
        missing_messages.append(PREDICTIONS_MISSING_MESSAGE)

    clusters = None
    if Path(DEFAULT_CLUSTERS_PATH).exists():
        clusters = load_clusters(str(DEFAULT_CLUSTERS_PATH))
    else:
        missing_messages.append(CLUSTERS_MISSING_MESSAGE)

    cluster_summary = pd.DataFrame()
    if Path(DEFAULT_SUMMARY_PATH).exists():
        cluster_summary = load_cluster_summary(str(DEFAULT_SUMMARY_PATH))
    elif clusters is not None:
        cluster_summary = build_cluster_summary_from_rows(clusters)
        missing_messages.append(SUMMARY_MISSING_MESSAGE)
    else:
        missing_messages.append(SUMMARY_MISSING_MESSAGE)

    regression_metrics = None
    if Path(DEFAULT_METRICS_PATH).exists():
        regression_metrics = load_metrics(str(DEFAULT_METRICS_PATH))
    else:
        missing_messages.append(REGRESSION_METRICS_MISSING_MESSAGE)

    cluster_metrics = None
    if CLUSTER_METRICS_PATH.exists():
        cluster_metrics = load_metrics(str(CLUSTER_METRICS_PATH))
    else:
        missing_messages.append(CLUSTER_METRICS_MISSING_MESSAGE)

    importance_df = pd.DataFrame(columns=["feature", "importance"])
    if Path(DEFAULT_MODEL_PATH).exists():
        model = load_model(str(DEFAULT_MODEL_PATH))
        importance_df = obtener_importancia_variables(model, top_n=15)

    render_missing_artifact_warnings(missing_messages)
    filters = render_sidebar(dataset, predictions, clusters)

    filtered_dataset = filter_data(dataset, filters, date_column="fecha_hora")
    filtered_predictions = filter_data(predictions, filters, date_column="fecha_hora_base")
    filtered_clusters = filter_data(clusters, filters, date_column="fecha_hora")
    filtered_cluster_summary = cluster_summary

    if not cluster_summary.empty:
        if filters["risk_levels"] and "nivel_riesgo" in filtered_cluster_summary.columns:
            filtered_cluster_summary = filtered_cluster_summary[
                filtered_cluster_summary["nivel_riesgo"].isin(filters["risk_levels"])
            ]

    selected_view = filters["view"]
    if selected_view == "executive":
        render_executive_view(filtered_dataset, filtered_predictions)
    elif selected_view == "technical":
        render_technical_view(
            filtered_predictions,
            regression_metrics,
            importance_df,
            filtered_clusters,
            filtered_cluster_summary,
            cluster_metrics,
        )
    else:
        render_citizen_view(filtered_dataset, filtered_predictions)

    render_footer(
        dataset=filtered_dataset if not filtered_dataset.empty else dataset,
        predictions=filtered_predictions,
        clusters=filtered_clusters,
    )


if __name__ == "__main__":
    main()
