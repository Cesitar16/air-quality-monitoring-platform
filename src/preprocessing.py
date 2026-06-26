from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

DATASET_URL = "http://localhost:8000/analytics/dataset-modelado"

COLUMNAS_CATEGORICAS = [
    "codigo_estacion",
    "comuna",
    "region",
    "tipo_sensor",
    "categoria_ica",
]

COLUMNAS_NUMERICAS = [
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

def cargar_dataset_desde_api(
    api_url: str = DATASET_URL,
    limit: int = 1000,
    timeout: int = 30,
) -> pd.DataFrame:
    """
    Descarga todos los registros del endpoint usando paginación.

    Parameters
    ----------
    api_url:
        URL completa del endpoint dataset-modelado.
    limit:
        Cantidad de registros solicitados en cada petición.
    timeout:
        Tiempo máximo de espera por petición, en segundos.

    Returns
    -------
    pd.DataFrame
        Dataset completo obtenido desde la API.
    """
    if limit < 1 or limit > 1000:
        raise ValueError("limit debe estar entre 1 y 1000.")

    registros: list[dict] = []
    offset = 0

    while True:
        parametros = {
            "limit": limit,
            "offset": offset,
        }

        try:
            respuesta = requests.get(
                api_url,
                params=parametros,
                timeout=timeout,
            )
            respuesta.raise_for_status()
        except requests.RequestException as error:
            raise ConnectionError(
                f"No fue posible obtener datos desde {api_url}."
            ) from error

        lote = respuesta.json()

        if not isinstance(lote, list):
            raise ValueError(
                "La API devolvió un formato inesperado. "
                "Se esperaba una lista de registros."
            )

        if not lote:
            break

        registros.extend(lote)
        print(f"Registros descargados: {len(registros)}")

        if len(lote) < limit:
            break

        offset += limit

    return pd.DataFrame(registros)

def cargar_dataset(
    fuente: str = "api",
    api_url: str = DATASET_URL,
    ruta_csv: str | Path = "data/processed/dataset_modelado.csv",
    limit: int = 1000,
    timeout: int = 30,
) -> pd.DataFrame:
    """
    Carga el dataset desde la API o desde un CSV.

    fuente="api":
        Usa el endpoint disponible.

    fuente="csv":
        Usa el archivo procesado entregado por el ETL.
    """
    fuente_normalizada = fuente.strip().lower()

    if fuente_normalizada == "api":
        return cargar_dataset_desde_api(
            api_url=api_url,
            limit=limit,
            timeout=timeout,
        )

    if fuente_normalizada == "csv":
        ruta = Path(ruta_csv)

        if not ruta.exists():
            raise FileNotFoundError(
                f"No existe el archivo solicitado: {ruta}"
            )

        return pd.read_csv(ruta)

    raise ValueError(
        "Fuente no válida. Usa 'api' o 'csv'."
    )

def preparar_fechas(df: pd.DataFrame) -> pd.DataFrame:
    #Convierte fecha_hora a datetime y crea variables temporales.
    
    resultado = df.copy()

    if "fecha_hora" not in resultado.columns:
        return resultado

    resultado["fecha_hora"] = pd.to_datetime(
        resultado["fecha_hora"],
        errors="coerce",
    )

    resultado["fecha"] = resultado["fecha_hora"].dt.date
    resultado["anio"] = resultado["fecha_hora"].dt.year
    resultado["mes"] = resultado["fecha_hora"].dt.month
    resultado["dia"] = resultado["fecha_hora"].dt.day
    resultado["hora"] = resultado["fecha_hora"].dt.hour
    resultado["dia_semana"] = resultado["fecha_hora"].dt.day_name()

    return resultado

def limpiar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    #Realiza una limpieza básica sin imputar datos para el clustering.
    
    if df.empty:
        return df.copy()

    resultado = preparar_fechas(df)

    # Limpiar espacios en columnas de texto.
    for columna in COLUMNAS_CATEGORICAS:
        if columna in resultado.columns:
            resultado[columna] = (
                resultado[columna]
                .astype("string")
                .str.strip()
            )

    # Convertir variables ambientales a formato numérico.
    for columna in COLUMNAS_NUMERICAS:
        if columna in resultado.columns:
            resultado[columna] = pd.to_numeric(
                resultado[columna],
                errors="coerce",
            )

    # Los contaminantes y la velocidad del viento no pueden ser negativos.
    columnas_no_negativas = [
        "mp25",
        "mp10",
        "so2",
        "no2",
        "velocidad_viento",
        "indice_vulnerabilidad_respiratoria",
        "emision_maxima_permitida",
    ]

    for columna in columnas_no_negativas:
        if columna in resultado.columns:
            resultado.loc[resultado[columna] < 0, columna] = pd.NA

    # Validar rangos meteorológicos básicos.
    if "humedad" in resultado.columns:
        resultado.loc[
            ~resultado["humedad"].between(0, 100),
            "humedad",
        ] = pd.NA

    if "direccion_viento_grados" in resultado.columns:
        resultado.loc[
            ~resultado["direccion_viento_grados"].between(0, 360),
            "direccion_viento_grados",
        ] = pd.NA

    if "temperatura" in resultado.columns:
        resultado.loc[
            ~resultado["temperatura"].between(-50, 60),
            "temperatura",
        ] = pd.NA

    # Eliminar registros duplicados por instante y estación.
    claves_duplicados = [
        columna
        for columna in ["fecha_hora", "codigo_estacion"]
        if columna in resultado.columns
    ]

    if claves_duplicados:
        resultado = resultado.drop_duplicates(
            subset=claves_duplicados,
            keep="first",
        )

    # Ordenar cronológicamente.
    columnas_orden = [
        columna
        for columna in [
            "fecha_hora",
            "region",
            "comuna",
            "codigo_estacion",
        ]
        if columna in resultado.columns
    ]

    if columnas_orden:
        resultado = resultado.sort_values(columnas_orden)

    return resultado.reset_index(drop=True)


def seleccionar_variables_numericas(
    df: pd.DataFrame,
    columnas: list[str],
) -> pd.DataFrame:
    #Selecciona las variables solicitadas que estén presentes en el dataset.
    
    columnas_disponibles = [
        columna
        for columna in columnas
        if columna in df.columns
    ]

    if not columnas_disponibles:
        raise ValueError(
            "Ninguna de las columnas solicitadas existe en el dataset."
        )

    resultado = df[columnas_disponibles].copy()

    for columna in columnas_disponibles:
        resultado[columna] = pd.to_numeric(
            resultado[columna],
            errors="coerce",
        )

    return resultado


def generar_resumen_calidad(df: pd.DataFrame) -> pd.DataFrame:
    #Resume el tipo de dato, cantidad de nulos y valores únicos.
    
    if df.empty:
        return pd.DataFrame(
            columns=[
                "columna",
                "tipo",
                "nulos",
                "porcentaje_nulos",
                "valores_unicos",
            ]
        )

    resumen = pd.DataFrame(
        {
            "columna": df.columns,
            "tipo": [str(df[columna].dtype) for columna in df.columns],
            "nulos": [df[columna].isna().sum() for columna in df.columns],
            "porcentaje_nulos": [
                round(df[columna].isna().mean() * 100, 2)
                for columna in df.columns
            ],
            "valores_unicos": [
                df[columna].nunique(dropna=True)
                for columna in df.columns
            ],
        }
    )

    return resumen


def guardar_dataset(
    df: pd.DataFrame,
    ruta: str | Path = "data/processed/dataset_modelado.csv",
) -> Path:
    #Guarda el DataFrame procesado como archivo CSV.
    ruta_salida = Path(ruta)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(
        ruta_salida,
        index=False,
        encoding="utf-8",
    )

    return ruta_salida


def main() -> None:
    print("Descargando dataset desde la API...")

    df_original = cargar_dataset_desde_api()
    df_limpio = limpiar_dataset(df_original)

    ruta_salida = guardar_dataset(df_limpio)
    resumen = generar_resumen_calidad(df_limpio)

    print("\nResultado del procesamiento")
    print("---------------------------")
    print(f"Filas originales: {len(df_original)}")
    print(f"Filas procesadas: {len(df_limpio)}")
    print(f"Columnas: {len(df_limpio.columns)}")
    print(f"Duplicados eliminados: {len(df_original) - len(df_limpio)}")

    print("\nResumen de calidad:")
    print(resumen.to_string(index=False))

    print(f"\nDataset guardado en: {ruta_salida}")


if __name__ == "__main__":
    main()