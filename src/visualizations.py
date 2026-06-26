from __future__ import annotations

from collections.abc import Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


VARIABLES_CORRELACION = [
    "mp25",
    "mp10",
    "so2",
    "no2",
    "velocidad_viento",
    "temperatura",
    "humedad",
    "indice_vulnerabilidad_respiratoria",
    "emision_maxima_permitida",
]


def validar_columnas(df: pd.DataFrame, columnas: Sequence[str]) -> None:
    faltantes = [columna for columna in columnas if columna not in df.columns]

    if faltantes:
        raise ValueError(
            "Faltan columnas necesarias: " + ", ".join(faltantes)
        )


def configurar_grafico(ax, titulo: str, etiqueta_x: str, etiqueta_y: str):
    ax.set_title(titulo)
    ax.set_xlabel(etiqueta_x)
    ax.set_ylabel(etiqueta_y)
    ax.grid(alpha=0.3)

    figura = ax.figure
    figura.tight_layout()

    return figura, ax


def graficar_mp25_por_comuna(df: pd.DataFrame, top_n: int = 15):
    validar_columnas(df, ["comuna", "mp25"])

    if top_n < 1:
        raise ValueError("top_n debe ser mayor que cero.")

    datos = df[["comuna", "mp25"]].copy()
    datos["mp25"] = pd.to_numeric(datos["mp25"], errors="coerce")
    datos = datos.dropna()

    promedio = (
        datos.groupby("comuna")["mp25"]
        .mean()
        .nlargest(top_n)
        .sort_values()
    )

    if promedio.empty:
        raise ValueError(
            "No existen datos válidos para graficar MP2.5 por comuna."
        )

    figura, ax = plt.subplots(figsize=(10, 6))
    ax.barh(promedio.index, promedio.values)

    return configurar_grafico(
        ax=ax,
        titulo=f"MP2.5 promedio por comuna - Top {top_n}",
        etiqueta_x="MP2.5 promedio",
        etiqueta_y="Comuna",
    )


def graficar_mp25_por_region(df: pd.DataFrame):
    validar_columnas(df, ["region", "mp25"])

    datos = df[["region", "mp25"]].copy()
    datos["mp25"] = pd.to_numeric(datos["mp25"], errors="coerce")
    datos = datos.dropna()

    promedio = datos.groupby("region")["mp25"].mean().sort_values()

    if promedio.empty:
        raise ValueError(
            "No existen datos válidos para graficar MP2.5 por región."
        )

    figura, ax = plt.subplots(figsize=(10, 6))
    ax.barh(promedio.index, promedio.values)

    return configurar_grafico(
        ax=ax,
        titulo="MP2.5 promedio por región",
        etiqueta_x="MP2.5 promedio",
        etiqueta_y="Región",
    )


def graficar_evolucion_mp25(df: pd.DataFrame, frecuencia: str = "D"):
    validar_columnas(df, ["fecha_hora", "mp25"])

    datos = df[["fecha_hora", "mp25"]].copy()

    datos["fecha_hora"] = pd.to_datetime(datos["fecha_hora"], errors="coerce")
    datos["mp25"] = pd.to_numeric(datos["mp25"], errors="coerce")
    datos = datos.dropna()

    evolucion = (
        datos.set_index("fecha_hora")["mp25"]
        .resample(frecuencia)
        .mean()
        .dropna()
    )

    if evolucion.empty:
        raise ValueError(
            "No existen datos válidos para graficar la evolución de MP2.5."
        )

    figura, ax = plt.subplots(figsize=(12, 5))
    ax.plot(evolucion.index, evolucion.values, marker="o")

    return configurar_grafico(
        ax=ax,
        titulo="Evolución temporal del MP2.5 promedio",
        etiqueta_x="Fecha",
        etiqueta_y="MP2.5 promedio",
    )


def graficar_ranking_sensores(df: pd.DataFrame, top_n: int = 10):
    validar_columnas(df, ["codigo_estacion", "mp25"])

    if top_n < 1:
        raise ValueError("top_n debe ser mayor que cero.")

    datos = df[["codigo_estacion", "mp25"]].copy()
    datos["mp25"] = pd.to_numeric(datos["mp25"], errors="coerce")
    datos = datos.dropna()

    ranking = (
        datos.groupby("codigo_estacion")["mp25"]
        .mean()
        .nlargest(top_n)
        .sort_values()
    )

    if ranking.empty:
        raise ValueError(
            "No existen datos válidos para graficar el ranking de sensores."
        )

    figura, ax = plt.subplots(figsize=(10, 6))
    ax.barh(ranking.index, ranking.values)

    return configurar_grafico(
        ax=ax,
        titulo=f"Sensores con mayor MP2.5 promedio - Top {top_n}",
        etiqueta_x="MP2.5 promedio",
        etiqueta_y="Código de estación",
    )


def graficar_dispersion(
    df: pd.DataFrame,
    variable_x: str,
    titulo: str | None = None,
):
    validar_columnas(df, [variable_x, "mp25"])

    datos = df[[variable_x, "mp25"]].copy()

    datos[variable_x] = pd.to_numeric(datos[variable_x], errors="coerce")
    datos["mp25"] = pd.to_numeric(datos["mp25"], errors="coerce")
    datos = datos.dropna()

    if datos.empty:
        raise ValueError(
            f"No existen datos válidos para comparar {variable_x} con MP2.5."
        )

    figura, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(datos[variable_x], datos["mp25"], alpha=0.6)

    if len(datos) >= 2 and datos[variable_x].nunique() > 1:
        pendiente, intercepto = np.polyfit(
            datos[variable_x],
            datos["mp25"],
            deg=1,
        )

        valores_x = np.linspace(
            datos[variable_x].min(),
            datos[variable_x].max(),
            100,
        )
        valores_y = pendiente * valores_x + intercepto

        ax.plot(
            valores_x,
            valores_y,
            linestyle="--",
            label="Tendencia lineal",
        )
        ax.legend()

    if titulo is None:
        titulo = f"Relación entre {variable_x} y MP2.5"

    return configurar_grafico(
        ax=ax,
        titulo=titulo,
        etiqueta_x=variable_x.replace("_", " ").title(),
        etiqueta_y="MP2.5",
    )


def graficar_correlaciones(
    df: pd.DataFrame,
    columnas: Sequence[str] | None = None,
):
    if columnas is None:
        columnas_solicitadas = VARIABLES_CORRELACION
    else:
        columnas_solicitadas = list(columnas)

    columnas_disponibles = [
        columna
        for columna in columnas_solicitadas
        if columna in df.columns
    ]

    if len(columnas_disponibles) < 2:
        raise ValueError(
            "Se necesitan al menos dos variables numéricas para calcular correlaciones."
        )

    datos = df[columnas_disponibles].copy()

    for columna in columnas_disponibles:
        datos[columna] = pd.to_numeric(datos[columna], errors="coerce")

    datos = datos.dropna(axis="columns", how="all")

    if datos.shape[1] < 2:
        raise ValueError(
            "No existen suficientes columnas con datos numéricos válidos."
        )

    correlaciones = datos.corr()

    figura, ax = plt.subplots(figsize=(10, 8))
    imagen = ax.imshow(correlaciones, vmin=-1, vmax=1, cmap="coolwarm")

    posiciones = range(len(correlaciones.columns))

    ax.set_xticks(posiciones)
    ax.set_yticks(posiciones)

    ax.set_xticklabels(correlaciones.columns, rotation=45, ha="right")
    ax.set_yticklabels(correlaciones.columns)

    for fila in range(len(correlaciones.index)):
        for columna in range(len(correlaciones.columns)):
            valor = correlaciones.iloc[fila, columna]
            ax.text(columna, fila, f"{valor:.2f}", ha="center", va="center")

    ax.set_title("Matriz de correlación de variables ambientales")
    figura.colorbar(imagen, ax=ax, label="Coeficiente de correlación")
    figura.tight_layout()

    return figura, ax


def graficar_clusters(
    df: pd.DataFrame,
    variable_x: str = "mp25",
    variable_y: str = "indice_vulnerabilidad_respiratoria",
    columna_cluster: str = "cluster",
    columna_etiqueta: str = "nivel_riesgo",
):
    validar_columnas(df, [variable_x, variable_y, columna_cluster])

    columnas = [variable_x, variable_y, columna_cluster]

    if columna_etiqueta in df.columns:
        columnas.append(columna_etiqueta)

    datos = df[columnas].copy()

    datos[variable_x] = pd.to_numeric(datos[variable_x], errors="coerce")
    datos[variable_y] = pd.to_numeric(datos[variable_y], errors="coerce")

    datos = datos.dropna(subset=[variable_x, variable_y, columna_cluster])

    if datos.empty:
        raise ValueError(
            "No existen datos válidos para visualizar los clusters."
        )

    figura, ax = plt.subplots(figsize=(9, 6))

    for cluster, grupo in datos.groupby(columna_cluster):
        if columna_etiqueta in grupo.columns:
            etiquetas = grupo[columna_etiqueta].dropna()

            if not etiquetas.empty:
                etiqueta = etiquetas.mode().iloc[0]
            else:
                etiqueta = f"Cluster {cluster}"
        else:
            etiqueta = f"Cluster {cluster}"

        ax.scatter(
            grupo[variable_x],
            grupo[variable_y],
            alpha=0.7,
            label=etiqueta,
        )

    ax.legend(title="Nivel de riesgo")

    return configurar_grafico(
        ax=ax,
        titulo="Clusters de riesgo ambiental",
        etiqueta_x=variable_x.replace("_", " ").title(),
        etiqueta_y=variable_y.replace("_", " ").title(),
    )