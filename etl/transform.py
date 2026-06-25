"""Transformation helpers for the ETL pipeline."""

import pandas as pd
from pandas.api.types import is_scalar


def normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza nombres de columnas: minusculas, sin espacios y con guion bajo."""
    df_normalizado = df.copy()
    df_normalizado.columns = [
        str(columna).strip().lower().replace(" ", "_")
        for columna in df_normalizado.columns
    ]
    return df_normalizado


def normalizar_texto(valor):
    """Normaliza texto eliminando espacios extra. Debe manejar None/NaN."""
    if valor is None or (is_scalar(valor) and pd.isna(valor)):
        return pd.NA

    texto = str(valor).strip()
    if not texto:
        return pd.NA
    return " ".join(texto.split())


def normalizar_region(valor):
    """Normaliza regiones del caso a los valores esperados por la BDD."""
    texto = normalizar_texto(valor)
    if texto is pd.NA:
        return pd.NA

    equivalencias = {
        "bio bio": "Biobío",
        "biobio": "Biobío",
        "bío bío": "Biobío",
        "biobío": "Biobío",
        "nuble": "Ñuble",
        "ñuble": "Ñuble",
        "ohiggins": "O'Higgins",
        "o higgins": "O'Higgins",
        "o'higgins": "O'Higgins",
        "maule": "Maule",
    }
    return equivalencias.get(texto.lower(), texto)


def normalizar_comuna(valor):
    """Normaliza nombres de comunas usados en las fuentes raw."""
    texto = normalizar_texto(valor)
    if texto is pd.NA:
        return pd.NA

    equivalencias = {
        "chillan": "Chillán",
        "chillán": "Chillán",
        "concepcion": "Concepción",
        "concepción": "Concepción",
        "curico": "Curicó",
        "curicó": "Curicó",
        "talca": "Talca",
        "rancagua": "Rancagua",
        "san fernando": "San Fernando",
        "san carlos": "San Carlos",
        "coronel": "Coronel",
        "hualpen": "Hualpén",
        "hualpén": "Hualpén",
    }
    return equivalencias.get(texto.lower(), texto)


def convertir_numero(valor):
    """Convierte números con coma decimal, strings y valores vacíos a float o NaN."""
    if valor is None or (is_scalar(valor) and pd.isna(valor)):
        return float("nan")

    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return float("nan")
        if texto.lower() in {"nr", "ausente", "nan"}:
            return float("nan")
        texto = texto.replace(",", ".")
        try:
            return float(texto)
        except ValueError:
            return float("nan")

    try:
        return float(valor)
    except (TypeError, ValueError):
        return float("nan")


def convertir_fecha(valor):
    """Convierte formatos de fecha mixtos a pandas datetime."""
    try:
        return pd.to_datetime(valor, errors="coerce", format="mixed", dayfirst=True)
    except TypeError:
        return pd.to_datetime(valor, errors="coerce", dayfirst=True)


def preparar_mediciones(df, fuente: str):
    """Normaliza una fuente de mediciones oficiales o comunitarias."""
    df_preparado = normalizar_columnas(df).copy()
    df_preparado["comuna"] = df_preparado["comuna"].apply(normalizar_comuna)
    df_preparado["region"] = df_preparado["region"].apply(normalizar_region)
    df_preparado["fecha_hora"] = df_preparado["fecha_hora"].apply(convertir_fecha)
    for columna in ("mp25", "mp10", "so2", "no2"):
        df_preparado[columna] = df_preparado[columna].apply(convertir_numero)

    df_preparado["fuente_dato"] = "oficial" if fuente == "oficial" else "comunitaria"
    return df_preparado[
        [
            "fecha_hora",
            "codigo_estacion",
            "comuna",
            "region",
            "mp25",
            "mp10",
            "so2",
            "no2",
            "fuente_dato",
        ]
    ].copy()


def preparar_clima(df):
    """Normaliza la fuente clima_historico."""
    df_preparado = normalizar_columnas(df).copy()
    df_preparado["comuna"] = df_preparado["comuna"].apply(normalizar_comuna)
    df_preparado["region"] = df_preparado["region"].apply(normalizar_region)
    df_preparado["fecha_hora"] = df_preparado["fecha_hora"].apply(convertir_fecha)
    for columna in (
        "velocidad_viento",
        "direccion_viento_grados",
        "temperatura",
        "humedad",
    ):
        df_preparado[columna] = df_preparado[columna].apply(convertir_numero)

    return df_preparado[
        [
            "fecha_hora",
            "comuna",
            "region",
            "velocidad_viento",
            "direccion_viento_grados",
            "temperatura",
            "humedad",
        ]
    ].copy()


def preparar_industrias(df):
    """Normaliza la fuente fiscalizacion_industrias."""
    df_preparado = normalizar_columnas(df).copy()
    df_preparado["comuna"] = df_preparado["comuna"].apply(normalizar_comuna)
    df_preparado["region"] = df_preparado["region"].apply(normalizar_region)
    df_preparado["rubro_industrial"] = df_preparado["rubro_industrial"].apply(
        normalizar_texto
    )
    df_preparado["emision_maxima_permitida"] = df_preparado[
        "emision_maxima_permitida"
    ].apply(convertir_numero)
    df_preparado["fecha_fiscalizacion"] = df_preparado["fecha_fiscalizacion"].apply(
        convertir_fecha
    )

    return df_preparado[
        [
            "nombre_industria",
            "rubro_industrial",
            "comuna",
            "region",
            "emision_maxima_permitida",
            "fecha_fiscalizacion",
            "observacion",
        ]
    ].copy()


def unir_mediciones_con_clima(df_mediciones, df_clima):
    """Une mediciones con clima por comuna, region y fecha/hora normalizada."""
    mediciones = df_mediciones.copy()
    clima = df_clima.copy()

    mediciones["fecha_hora_redondeada"] = mediciones["fecha_hora"].dt.floor("h")
    clima["fecha_hora_redondeada"] = clima["fecha_hora"].dt.floor("h")

    clima_para_merge = clima[
        [
            "comuna",
            "region",
            "fecha_hora_redondeada",
            "velocidad_viento",
            "direccion_viento_grados",
            "temperatura",
            "humedad",
        ]
    ]

    resultado = mediciones.merge(
        clima_para_merge,
        on=["comuna", "region", "fecha_hora_redondeada"],
        how="left",
    ).drop(columns=["fecha_hora_redondeada"])

    return resultado[
        [
            "fecha_hora",
            "codigo_estacion",
            "comuna",
            "region",
            "mp25",
            "mp10",
            "so2",
            "no2",
            "velocidad_viento",
            "direccion_viento_grados",
            "temperatura",
            "humedad",
            "fuente_dato",
        ]
    ].copy()


def transformar_fuentes(fuentes: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Ejecuta la transformación base de todas las fuentes."""
    mediciones_oficiales = preparar_mediciones(
        fuentes["mediciones_oficiales"],
        fuente="oficial",
    )
    sensores_comunitarios = preparar_mediciones(
        fuentes["sensores_comunitarios"],
        fuente="comunitaria",
    )
    clima_limpio = preparar_clima(fuentes["clima_historico"])
    industrias_limpias = preparar_industrias(fuentes["fiscalizacion_industrias"])

    mediciones_unificadas = pd.concat(
        [mediciones_oficiales, sensores_comunitarios],
        ignore_index=True,
    )
    mediciones_limpias = unir_mediciones_con_clima(
        mediciones_unificadas,
        clima_limpio,
    )

    return {
        "mediciones_limpias": mediciones_limpias,
        "industrias_limpias": industrias_limpias,
        "clima_limpio": clima_limpio,
    }
