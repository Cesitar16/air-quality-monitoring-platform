from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


VARIABLES_SUGERIDAS = [
    "mp25",
    "mp10",
    "temperatura",
    "humedad",
    "velocidad_viento",
    "emision_maxima_permitida",
    "indice_vulnerabilidad_respiratoria",
]

# Estos pesos permiten ordenar los clusters según riesgo relativo.
# No reemplazan una clasificación ambiental oficial.
PESOS_RIESGO = {
    "mp25": (0.45, "directa"),
    "mp10": (0.15, "directa"),
    "so2": (0.08, "directa"),
    "no2": (0.08, "directa"),
    "humedad": (0.04, "directa"),
    "indice_vulnerabilidad_respiratoria": (0.12, "directa"),
    "emision_maxima_permitida": (0.04, "directa"),
    "velocidad_viento": (0.04, "inversa"),
}


def preparar_variables_clustering(
    df: pd.DataFrame,
    columnas: Optional[Sequence[str]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Convierte variables a números, elimina columnas inútiles
    e imputa valores nulos mediante la mediana.
    """
    if df.empty:
        raise ValueError("El DataFrame está vacío.")

    if columnas is None:
        solicitadas = VARIABLES_SUGERIDAS
    else:
        solicitadas = list(columnas)

    disponibles = [
        columna
        for columna in solicitadas
        if columna in df.columns
    ]

    if len(disponibles) < 2:
        raise ValueError(
            "Se necesitan al menos dos variables para clustering."
        )

    datos = df[disponibles].copy()

    for columna in datos.columns:
        datos[columna] = pd.to_numeric(
            datos[columna],
            errors="coerce",
        )

    columnas_inutiles = [
        columna
        for columna in datos.columns
        if datos[columna].notna().sum() == 0
        or datos[columna].nunique(dropna=True) <= 1
    ]

    if columnas_inutiles:
        datos = datos.drop(columns=columnas_inutiles)

    if datos.shape[1] < 2:
        raise ValueError(
            "Quedan menos de dos variables útiles "
            "después de la limpieza."
        )

    medianas = datos.median(numeric_only=True)
    datos = datos.fillna(medianas)

    if datos.isna().any().any():
        raise ValueError(
            "No fue posible resolver todos los valores nulos."
        )

    return datos.astype(float), list(datos.columns)


def escalar_variables(
    df: pd.DataFrame,
    columnas: Optional[Sequence[str]] = None,
) -> Tuple[
    np.ndarray,
    StandardScaler,
    pd.DataFrame,
    List[str],
]:
    """
    Prepara y estandariza las variables mediante StandardScaler.
    """
    datos, columnas_utilizadas = preparar_variables_clustering(
        df,
        columnas,
    )

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(datos)

    return (
        X_scaled,
        scaler,
        datos,
        columnas_utilizadas,
    )


def entrenar_kmeans(
    X_scaled: np.ndarray,
    n_clusters: int = 3,
    random_state: int = 42,
) -> KMeans:
    """
    Entrena un modelo K-Means reproducible.
    """
    matriz = np.asarray(
        X_scaled,
        dtype=float,
    )

    if matriz.ndim != 2:
        raise ValueError(
            "X_scaled debe tener dos dimensiones."
        )

    if n_clusters < 2:
        raise ValueError(
            "n_clusters debe ser al menos 2."
        )

    if matriz.shape[0] < n_clusters:
        raise ValueError(
            "No hay suficientes registros para esa cantidad de clusters."
        )

    if not np.isfinite(matriz).all():
        raise ValueError(
            "X_scaled contiene valores nulos o infinitos."
        )

    modelo = KMeans(
        n_clusters=n_clusters,
        random_state=random_state,
        n_init=10,
    )

    modelo.fit(matriz)

    return modelo


def evaluar_numero_clusters(
    X_scaled: np.ndarray,
    min_clusters: int = 2,
    max_clusters: int = 6,
    random_state: int = 42,
    max_muestra_silhouette: int = 5000,
) -> pd.DataFrame:
    """
    Calcula inercia y silhouette para distintos valores de K.

    Para evitar un cálculo demasiado pesado, silhouette utiliza
    como máximo una muestra de 5000 registros.
    """
    matriz = np.asarray(
        X_scaled,
        dtype=float,
    )

    if matriz.ndim != 2:
        raise ValueError(
            "X_scaled debe tener dos dimensiones."
        )

    if matriz.shape[0] < 3:
        raise ValueError(
            "Se necesitan al menos tres registros válidos."
        )

    limite_superior = min(
        max_clusters,
        matriz.shape[0] - 1,
    )

    if min_clusters < 2 or min_clusters > limite_superior:
        raise ValueError(
            "El rango de clusters no es válido."
        )

    resultados = []

    for cantidad in range(
        min_clusters,
        limite_superior + 1,
    ):
        modelo = entrenar_kmeans(
            matriz,
            n_clusters=cantidad,
            random_state=random_state,
        )

        etiquetas = modelo.labels_

        tamano_muestra = min(
            max_muestra_silhouette,
            matriz.shape[0],
        )

        silhouette = silhouette_score(
            matriz,
            etiquetas,
            sample_size=tamano_muestra,
            random_state=random_state,
        )

        resultados.append(
            {
                "n_clusters": cantidad,
                "inercia": modelo.inertia_,
                "silhouette": silhouette,
            }
        )

    return pd.DataFrame(resultados)


def agregar_clusters(
    df: pd.DataFrame,
    modelo: KMeans,
    X_scaled: np.ndarray,
    columna_cluster: str = "cluster",
) -> pd.DataFrame:
    """
    Agrega el cluster predicho a cada fila del DataFrame.
    """
    matriz = np.asarray(
        X_scaled,
        dtype=float,
    )

    if len(df) != matriz.shape[0]:
        raise ValueError(
            "La cantidad de filas no coincide con X_scaled."
        )

    resultado = df.copy()

    resultado[columna_cluster] = modelo.predict(
        matriz
    )

    return resultado


def obtener_centroides(
    modelo: KMeans,
    scaler: StandardScaler,
    columnas: Sequence[str],
) -> pd.DataFrame:
    """
    Devuelve los centroides en las unidades originales.
    """
    cantidad_variables = modelo.cluster_centers_.shape[1]

    if cantidad_variables != len(columnas):
        raise ValueError(
            "Las columnas no coinciden con las dimensiones "
            "de los centroides."
        )

    valores_originales = scaler.inverse_transform(
        modelo.cluster_centers_
    )

    centroides = pd.DataFrame(
        valores_originales,
        columns=list(columnas),
    )

    centroides.insert(
        0,
        "cluster",
        range(len(centroides)),
    )

    return centroides


def _normalizar(serie: pd.Series) -> pd.Series:
    """
    Normaliza una serie entre 0 y 1.
    """
    minimo = serie.min()
    maximo = serie.max()

    if (
        pd.isna(minimo)
        or pd.isna(maximo)
        or minimo == maximo
    ):
        return pd.Series(
            0.0,
            index=serie.index,
        )

    return (serie - minimo) / (maximo - minimo)


def calcular_perfil_clusters(
    df: pd.DataFrame,
    columna_cluster: str = "cluster",
) -> pd.DataFrame:
    """
    Resume los clusters y calcula un puntaje relativo de riesgo.

    El puntaje prioriza los contaminantes y la vulnerabilidad.
    La velocidad del viento se interpreta de forma inversa:
    una mayor ventilación reduce el puntaje relativo.
    """
    if columna_cluster not in df.columns:
        raise ValueError(
            "No existe la columna de cluster."
        )

    variables = [
        columna
        for columna in PESOS_RIESGO
        if columna in df.columns
    ]

    if not variables:
        raise ValueError(
            "No existen variables para interpretar los clusters."
        )

    datos = df[
        [columna_cluster] + variables
    ].copy()

    for columna in variables:
        datos[columna] = pd.to_numeric(
            datos[columna],
            errors="coerce",
        )

    perfil = (
        datos.groupby(columna_cluster)[variables]
        .mean()
    )

    cantidades = datos.groupby(
        columna_cluster
    ).size()

    perfil.insert(
        0,
        "cantidad_registros",
        cantidades,
    )

    perfil["puntaje_riesgo"] = 0.0
    peso_total = 0.0

    for variable in variables:
        serie = perfil[variable]

        if serie.notna().sum() == 0:
            continue

        peso, direccion = PESOS_RIESGO[variable]

        serie = serie.fillna(
            serie.median()
        )

        valores_normalizados = _normalizar(
            serie
        )

        if direccion == "inversa":
            valores_normalizados = (
                1.0 - valores_normalizados
            )

        perfil["puntaje_riesgo"] += (
            peso * valores_normalizados
        )

        peso_total += peso

    if peso_total == 0:
        raise ValueError(
            "No fue posible calcular el puntaje de riesgo."
        )

    perfil["puntaje_riesgo"] /= peso_total

    return perfil.reset_index()


def _crear_mapa_riesgo(
    perfil: pd.DataFrame,
) -> Dict[int, str]:
    """
    Ordena los clusters y les asigna etiquetas interpretables.
    """
    clusters_ordenados = (
        perfil.sort_values("puntaje_riesgo")["cluster"]
        .astype(int)
        .tolist()
    )

    cantidad_clusters = len(
        clusters_ordenados
    )

    etiquetas_disponibles = {
        2: [
            "Bajo riesgo",
            "Riesgo crítico",
        ],
        3: [
            "Bajo riesgo",
            "Riesgo moderado",
            "Riesgo crítico",
        ],
        4: [
            "Bajo riesgo",
            "Riesgo moderado",
            "Riesgo alto",
            "Riesgo crítico",
        ],
    }

    etiquetas = etiquetas_disponibles.get(
        cantidad_clusters,
        [
            "Nivel de riesgo " + str(indice + 1)
            for indice in range(cantidad_clusters)
        ],
    )

    return dict(
        zip(
            clusters_ordenados,
            etiquetas,
        )
    )


def asignar_etiquetas_riesgo(
    df: pd.DataFrame,
    columna_cluster: str = "cluster",
    columna_salida: str = "nivel_riesgo",
) -> pd.DataFrame:
    """
    Traduce los números de cluster a etiquetas de riesgo.
    """
    perfil = calcular_perfil_clusters(
        df,
        columna_cluster,
    )

    mapa_riesgo = _crear_mapa_riesgo(
        perfil
    )

    resultado = df.copy()

    resultado[columna_salida] = (
        resultado[columna_cluster]
        .map(mapa_riesgo)
    )

    return resultado


def resumir_clusters(
    df: pd.DataFrame,
    columna_cluster: str = "cluster",
) -> pd.DataFrame:
    """
    Devuelve el perfil, puntaje y etiqueta de cada cluster.
    """
    perfil = calcular_perfil_clusters(
        df,
        columna_cluster,
    )

    mapa_riesgo = _crear_mapa_riesgo(
        perfil
    )

    perfil["nivel_riesgo"] = (
        perfil[columna_cluster]
        .map(mapa_riesgo)
    )

    perfil = (
        perfil.sort_values("puntaje_riesgo")
        .reset_index(drop=True)
    )

    primeras_columnas = [
        columna_cluster,
        "nivel_riesgo",
        "cantidad_registros",
        "puntaje_riesgo",
    ]

    columnas_restantes = [
        columna
        for columna in perfil.columns
        if columna not in primeras_columnas
    ]

    return perfil[
        primeras_columnas
        + columnas_restantes
    ]