"""Validation helpers for the ETL pipeline."""

import pandas as pd

COLUMNAS_MEDICION_FINAL = [
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


def validar_columnas_requeridas(
    df: pd.DataFrame,
    columnas_requeridas: list[str],
) -> None:
    """Valida que el DataFrame incluya todas las columnas requeridas."""
    columnas_faltantes = [
        columna for columna in columnas_requeridas if columna not in df.columns
    ]
    if columnas_faltantes:
        faltantes = ", ".join(columnas_faltantes)
        raise ValueError(f"Faltan columnas requeridas: {faltantes}")


def _es_vacio(valor) -> bool:
    """Retorna True si el valor es nulo, vacio o solo espacios."""
    if pd.isna(valor):
        return True
    if isinstance(valor, str):
        return not valor.strip()
    return False


def _agregar_error(errores: list[str], condicion: bool, mensaje: str) -> None:
    """Agrega un mensaje de error si se cumple la condicion."""
    if condicion:
        errores.append(mensaje)


def _detectar_duplicados(df: pd.DataFrame) -> pd.Series:
    """Detecta duplicados conservando la primera ocurrencia como valida."""
    return df.duplicated(subset=["codigo_estacion", "fecha_hora"], keep="first")


def validar_mediciones(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Valida mediciones ambientales y separa filas validas e invalidas."""
    validar_columnas_requeridas(df, COLUMNAS_MEDICION_FINAL)

    columnas_error = list(df.columns) + ["numero_fila", "motivo_error", "fase"]
    duplicados = _detectar_duplicados(df)

    filas_validas: list[dict] = []
    filas_error: list[dict] = []

    for numero_fila, fila in df.reset_index(drop=True).iterrows():
        errores: list[str] = []

        _agregar_error(errores, pd.isna(fila["fecha_hora"]), "fecha_hora nula")
        _agregar_error(errores, _es_vacio(fila["codigo_estacion"]), "codigo_estacion vacio")
        _agregar_error(errores, _es_vacio(fila["comuna"]), "comuna vacia")
        _agregar_error(errores, _es_vacio(fila["region"]), "region vacia")

        for columna in ("mp25", "mp10", "so2", "no2"):
            valor = fila[columna]
            _agregar_error(errores, pd.isna(valor), f"{columna} faltante")
            _agregar_error(
                errores,
                pd.notna(valor) and valor < 0,
                f"{columna} negativo",
            )

        velocidad = fila["velocidad_viento"]
        direccion = fila["direccion_viento_grados"]
        temperatura = fila["temperatura"]
        humedad = fila["humedad"]

        _agregar_error(
            errores,
            pd.notna(velocidad) and velocidad < 0,
            "velocidad_viento negativa",
        )
        _agregar_error(
            errores,
            pd.notna(direccion) and not 0 <= direccion <= 360,
            "direccion_viento_grados fuera de rango",
        )
        _agregar_error(
            errores,
            pd.notna(temperatura) and not -50 <= temperatura <= 60,
            "temperatura fuera de rango",
        )
        _agregar_error(
            errores,
            pd.notna(humedad) and not 0 <= humedad <= 100,
            "humedad fuera de rango",
        )

        _agregar_error(
            errores,
            fila["fuente_dato"] not in {"oficial", "comunitaria"},
            "fuente_dato invalida",
        )
        _agregar_error(
            errores,
            bool(duplicados.iloc[numero_fila]),
            "duplicado codigo_estacion+fecha_hora",
        )

        if errores:
            fila_error = fila.to_dict()
            fila_error["numero_fila"] = numero_fila
            fila_error["motivo_error"] = "; ".join(errores)
            fila_error["fase"] = "validate"
            filas_error.append(fila_error)
        else:
            filas_validas.append(fila.to_dict())

    mediciones_validas = pd.DataFrame(filas_validas, columns=df.columns)
    errores_etl = pd.DataFrame(filas_error, columns=columnas_error)
    if errores_etl.empty:
        errores_etl = pd.DataFrame(columns=columnas_error)

    return mediciones_validas, errores_etl
