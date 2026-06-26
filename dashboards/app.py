"""Streamlit dashboard for historical monitoring and MP2.5 forecasts."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.clustering import (  # noqa: E402
    DEFAULT_CLUSTERS_PATH,
    DEFAULT_SUMMARY_PATH,
)
from src.regression import (  # noqa: E402
    DEFAULT_DATASET_PATH,
    DEFAULT_METRICS_PATH,
    DEFAULT_MODEL_PATH,
    DEFAULT_PREDICTIONS_PATH,
    cargar_metricas,
    cargar_modelo,
    clasificar_mp25,
    obtener_importancia_variables,
)


st.set_page_config(
    page_title="Monitoreo y Pronostico MP2.5",
    page_icon="AQ",
    layout="wide",
)


@st.cache_data(show_spinner=False)
def cargar_dataset(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def cargar_predicciones(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    for columna in ("fecha_hora_base", "fecha_hora_objetivo", "fecha_hora"):
        df[columna] = pd.to_datetime(df[columna], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def cargar_clusters(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "fecha_hora" in df.columns:
        df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
    return df


@st.cache_data(show_spinner=False)
def cargar_resumen_clusters(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


@st.cache_resource(show_spinner=False)
def cargar_modelo_dashboard(path: str):
    return cargar_modelo(path)


def filtrar_por_sidebar(
    df: pd.DataFrame,
    *,
    region: list[str],
    comuna: list[str],
    tipo_sensor: list[str],
    fecha_inicio: pd.Timestamp,
    fecha_fin: pd.Timestamp,
    columna_fecha: str,
) -> pd.DataFrame:
    filtrado = df.copy()
    if region:
        filtrado = filtrado[filtrado["region"].isin(region)]
    if comuna:
        filtrado = filtrado[filtrado["comuna"].isin(comuna)]
    if tipo_sensor and "tipo_sensor" in filtrado.columns:
        filtrado = filtrado[filtrado["tipo_sensor"].isin(tipo_sensor)]
    filtrado = filtrado[
        (filtrado[columna_fecha] >= fecha_inicio) & (filtrado[columna_fecha] <= fecha_fin)
    ]
    return filtrado


def render_metricas(metricas: dict) -> None:
    columnas = st.columns(len(metricas["models"]))
    for columna, (nombre, valores) in zip(columnas, metricas["models"].items()):
        columna.metric(f"{nombre} RMSE", f"{valores['rmse']:.2f}")
        columna.caption(
            f"MAE {valores['mae']:.2f} | R2 {valores['r2']:.3f}"
        )


def render_vista_ejecutiva(dataset: pd.DataFrame, pronostico: pd.DataFrame) -> None:
    st.subheader("Vista Ejecutiva")
    if dataset.empty or pronostico.empty:
        st.info("No hay datos suficientes para la vista ejecutiva con los filtros actuales.")
        return

    comuna_critica = (
        dataset.groupby("comuna", as_index=False)["mp25"]
        .mean()
        .sort_values("mp25", ascending=False)
        .iloc[0]
    )
    prediccion_promedio = pronostico["mp25_predicho"].mean()
    alertas_altas = int((pronostico["mp25_predicho"] >= 80).sum())

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("MP2.5 promedio", f"{dataset['mp25'].mean():.2f}")
    col2.metric("MP2.5 maximo", f"{dataset['mp25'].max():.2f}")
    col3.metric("Comuna critica", comuna_critica["comuna"])
    col4.metric("Pronostico promedio 24h", f"{prediccion_promedio:.2f}", delta=f"{alertas_altas} alertas >= 80")

    ranking_comunas = (
        pronostico.groupby(["comuna", "region"], as_index=False)["mp25_predicho"]
        .mean()
        .sort_values("mp25_predicho", ascending=False)
    )

    grafico_ranking = px.bar(
        ranking_comunas,
        x="comuna",
        y="mp25_predicho",
        color="region",
        title="Ranking de comunas por MP2.5 predicho a 24h",
        labels={"mp25_predicho": "MP2.5 predicho", "comuna": "Comuna"},
    )
    st.plotly_chart(grafico_ranking, use_container_width=True)

    st.dataframe(
        ranking_comunas.rename(columns={"mp25_predicho": "mp25_predicho_promedio"}),
        use_container_width=True,
        hide_index=True,
    )


def render_vista_tecnica(
    evaluacion: pd.DataFrame,
    metricas: dict,
    importancia_df: pd.DataFrame,
    clusters: pd.DataFrame,
    resumen_clusters: pd.DataFrame,
) -> None:
    st.subheader("Vista Tecnica")
    render_metricas(metricas)

    col1, col2 = st.columns([1.4, 1])
    with col1:
        if evaluacion.empty:
            st.info("No hay filas de evaluacion para los filtros actuales.")
        else:
            scatter = px.scatter(
                evaluacion,
                x="mp25_real",
                y="mp25_predicho",
                color="comuna",
                title="Comparacion real vs predicho",
                labels={"mp25_real": "MP2.5 real", "mp25_predicho": "MP2.5 predicho"},
                hover_data=["codigo_estacion", "fecha_hora_base", "fecha_hora_objetivo"],
            )
            minimo = min(evaluacion["mp25_real"].min(), evaluacion["mp25_predicho"].min())
            maximo = max(evaluacion["mp25_real"].max(), evaluacion["mp25_predicho"].max())
            scatter.add_shape(
                type="line",
                x0=minimo,
                y0=minimo,
                x1=maximo,
                y1=maximo,
                line={"dash": "dash"},
            )
            st.plotly_chart(scatter, use_container_width=True)

    with col2:
        if importancia_df.empty:
            st.info("El modelo seleccionado no expone importancia de variables.")
        else:
            grafico_importancia = px.bar(
                importancia_df.sort_values("importance"),
                x="importance",
                y="feature",
                orientation="h",
                title="Importancia de variables",
                labels={"importance": "Importancia", "feature": "Variable"},
            )
            st.plotly_chart(grafico_importancia, use_container_width=True)

    if not resumen_clusters.empty:
        col3, col4 = st.columns([1, 1.4])
        with col3:
            distribucion_clusters = (
                clusters.groupby("nivel_riesgo", as_index=False)
                .size()
                .rename(columns={"size": "cantidad"})
                .sort_values("cantidad", ascending=False)
            )
            grafico_clusters = px.bar(
                distribucion_clusters,
                x="nivel_riesgo",
                y="cantidad",
                color="nivel_riesgo",
                title="Distribucion de clusters de riesgo",
                labels={"nivel_riesgo": "Nivel de riesgo", "cantidad": "Registros"},
            )
            st.plotly_chart(grafico_clusters, use_container_width=True)

        with col4:
            tabla_resumen = resumen_clusters.copy()
            if "puntaje_riesgo" in tabla_resumen.columns:
                tabla_resumen = tabla_resumen.sort_values("puntaje_riesgo", ascending=False)
            st.dataframe(
                tabla_resumen,
                use_container_width=True,
                hide_index=True,
            )

    if not evaluacion.empty:
        st.dataframe(
            evaluacion.sort_values("fecha_hora_base", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


def render_vista_ciudadana(dataset: pd.DataFrame, pronostico: pd.DataFrame) -> None:
    st.subheader("Vista Ciudadana")
    if pronostico.empty or dataset.empty:
        st.info("No hay pronosticos para los filtros actuales.")
        return

    resumen_comuna = (
        pronostico.groupby(["comuna", "region"], as_index=False)
        .agg(
            mp25_predicho=("mp25_predicho", "mean"),
            fecha_hora_objetivo=("fecha_hora_objetivo", "max"),
            estaciones=("codigo_estacion", "nunique"),
        )
        .sort_values("comuna")
    )

    comuna_seleccionada = st.selectbox("Selecciona una comuna", resumen_comuna["comuna"])
    fila = resumen_comuna.loc[resumen_comuna["comuna"] == comuna_seleccionada].iloc[0]
    clasificacion = clasificar_mp25(float(fila["mp25_predicho"]))
    ultimo_estado = (
        dataset.loc[dataset["comuna"] == comuna_seleccionada]
        .sort_values("fecha_hora")
        .tail(1)
    )
    mp25_actual = float(ultimo_estado["mp25"].iloc[0]) if not ultimo_estado.empty else float("nan")
    clasificacion_actual = clasificar_mp25(mp25_actual) if not pd.isna(mp25_actual) else clasificacion

    col1, col2, col3 = st.columns(3)
    col1.metric("Estado actual", clasificacion_actual["categoria"])
    col2.metric("Pronostico 24h", f"{fila['mp25_predicho']:.2f}")
    col3.metric("Estaciones consideradas", int(fila["estaciones"]))

    st.markdown(
        f"""
        **Comuna:** {fila['comuna']} ({fila['region']})  
        **MP2.5 actual:** {mp25_actual:.2f}  
        **Fecha objetivo:** {fila['fecha_hora_objetivo']}  
        **Color referencial:** {clasificacion['color_referencial']}  
        **Mensaje:** {clasificacion['mensaje_ciudadano']}
        """
    )

    detalle = pronostico.loc[
        pronostico["comuna"] == comuna_seleccionada,
        [
            "codigo_estacion",
            "tipo_sensor",
            "fecha_hora_base",
            "fecha_hora_objetivo",
            "mp25_actual",
            "mp25_predicho",
            "categoria_predicha",
        ],
    ].sort_values("mp25_predicho", ascending=False)
    st.dataframe(detalle, use_container_width=True, hide_index=True)


def main() -> None:
    st.title("Monitoreo de Calidad del Aire y Pronostico MP2.5")

    dataset_path = DEFAULT_DATASET_PATH
    predictions_path = DEFAULT_PREDICTIONS_PATH
    metrics_path = DEFAULT_METRICS_PATH
    model_path = DEFAULT_MODEL_PATH
    clusters_path = DEFAULT_CLUSTERS_PATH
    summary_path = DEFAULT_SUMMARY_PATH

    faltantes = [
        str(path)
        for path in (dataset_path, predictions_path, metrics_path, clusters_path, summary_path)
        if not Path(path).exists()
    ]
    if faltantes:
        st.error(
            "Faltan artefactos requeridos. Ejecuta primero `python src/clustering.py` y `python src/regression.py`.\n\n"
            + "\n".join(faltantes)
        )
        st.stop()

    dataset = cargar_dataset(str(dataset_path))
    predicciones = cargar_predicciones(str(predictions_path))
    clusters = cargar_clusters(str(clusters_path))
    resumen_clusters = cargar_resumen_clusters(str(summary_path))
    metricas = cargar_metricas(metrics_path)
    importancia_df = pd.DataFrame(columns=["feature", "importance"])
    if Path(model_path).exists():
        modelo = cargar_modelo_dashboard(str(model_path))
        importancia_df = obtener_importancia_variables(modelo, top_n=15)

    min_fecha = dataset["fecha_hora"].min().date()
    max_fecha = dataset["fecha_hora"].max().date()

    st.sidebar.header("Filtros globales")
    regiones = sorted(dataset["region"].dropna().unique().tolist())
    comunas = sorted(dataset["comuna"].dropna().unique().tolist())
    tipos_sensor = sorted(dataset["tipo_sensor"].dropna().unique().tolist())

    regiones_sel = st.sidebar.multiselect("Region", regiones)
    comunas_sel = st.sidebar.multiselect("Comuna", comunas)
    tipos_sel = st.sidebar.multiselect("Tipo de sensor", tipos_sensor)
    rango_fechas = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_fecha, max_fecha),
        min_value=min_fecha,
        max_value=max_fecha,
    )

    fecha_inicio = pd.Timestamp(rango_fechas[0])
    fecha_fin = pd.Timestamp(rango_fechas[-1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

    dataset_filtrado = filtrar_por_sidebar(
        dataset,
        region=regiones_sel,
        comuna=comunas_sel,
        tipo_sensor=tipos_sel,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        columna_fecha="fecha_hora",
    )
    predicciones_filtradas = filtrar_por_sidebar(
        predicciones,
        region=regiones_sel,
        comuna=comunas_sel,
        tipo_sensor=tipos_sel,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        columna_fecha="fecha_hora_base",
    )
    clusters_filtrados = filtrar_por_sidebar(
        clusters,
        region=regiones_sel,
        comuna=comunas_sel,
        tipo_sensor=tipos_sel,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        columna_fecha="fecha_hora",
    )
    resumen_clusters_filtrado = (
        clusters_filtrados.groupby(["cluster", "nivel_riesgo"], as_index=False)
        .agg(
            cantidad_registros=("codigo_estacion", "size"),
            mp25=("mp25", "mean"),
            mp10=("mp10", "mean"),
            velocidad_viento=("velocidad_viento", "mean"),
            temperatura=("temperatura", "mean"),
        )
        .rename(columns={"mp25": "mp25_promedio", "mp10": "mp10_promedio"})
    )
    if resumen_clusters_filtrado.empty:
        resumen_clusters_filtrado = resumen_clusters.copy()

    evaluacion = predicciones_filtradas.loc[
        predicciones_filtradas["tipo_registro"] == "evaluacion"
    ].copy()
    pronostico = predicciones_filtradas.loc[
        predicciones_filtradas["tipo_registro"] == "pronostico_24h"
    ].copy()

    tab1, tab2, tab3 = st.tabs(
        ["Vista Ejecutiva", "Vista Tecnica", "Vista Ciudadana"]
    )
    with tab1:
        render_vista_ejecutiva(dataset_filtrado, pronostico)
    with tab2:
        render_vista_tecnica(
            evaluacion,
            metricas,
            importancia_df,
            clusters_filtrados,
            resumen_clusters_filtrado,
        )
    with tab3:
        render_vista_ciudadana(dataset_filtrado, pronostico)


if __name__ == "__main__":
    main()
