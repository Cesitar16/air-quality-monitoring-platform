"""Loading layer for the ETL pipeline."""

from __future__ import annotations

import json

import pandas as pd
import requests

from etl import config
from etl.transform import normalizar_comuna

MAPEO_ESTACIONES_COLUMNS = [
    "codigo_estacion_raw",
    "codigo_unico_api",
    "comuna",
    "region",
    "fuente_dato",
    "tipo_sensor_api",
]

CLIMA_REQUERIDO_API_COLUMNS = [
    "velocidad_viento",
    "direccion_viento_grados",
    "temperatura",
    "humedad",
]

OMITIDAS_COLUMNS = [
    "codigo_estacion",
    "codigo_unico_api",
    "id_estacion",
    "comuna",
    "region",
    "fuente_dato",
    "fecha_hora",
    "motivo_omision",
    "modo_mapeo",
]

PAYLOAD_METADATA_FIELDS = {
    "_codigo_estacion",
    "_codigo_unico_api",
    "_comuna",
    "_region",
    "_fuente_dato",
    "_modo_mapeo",
}


def _manejar_error_api(
    mensaje: str,
    strict: bool,
    default,
):
    if strict:
        raise RuntimeError(mensaje)
    return default


def _serializar_valor(valor):
    if pd.isna(valor):
        return None
    return valor if isinstance(valor, str) else float(valor)


def _serializar_fecha(valor) -> str | None:
    if pd.isna(valor):
        return None
    return pd.Timestamp(valor).isoformat()


def _normalizar_fecha_clave(valor) -> str | None:
    if valor is None or pd.isna(valor):
        return None
    return pd.Timestamp(valor).isoformat()


def _payload_envio(payload: list[dict]) -> list[dict]:
    return [
        {clave: valor for clave, valor in item.items() if clave not in PAYLOAD_METADATA_FIELDS}
        for item in payload
    ]


def verificar_api_disponible(timeout: int = 5) -> bool:
    """Verifica si la API responde correctamente en /health."""
    try:
        response = requests.get(config.API_HEALTH_URL, timeout=timeout)
        return response.status_code == 200
    except Exception:
        return False


def obtener_estaciones_api(strict: bool = False) -> list[dict]:
    """Obtiene estaciones desde la API."""
    try:
        response = requests.get(config.API_ESTACIONES_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return _manejar_error_api(
                "La API devolvio una estructura invalida en /estaciones.",
                strict,
                [],
            )
        return data
    except (requests.RequestException, ValueError) as exc:
        return _manejar_error_api(
            f"No fue posible obtener estaciones desde la API: {exc}",
            strict,
            [],
        )


def obtener_comunas_api(strict: bool = False) -> list[dict]:
    """Obtiene comunas desde la API."""
    try:
        response = requests.get(config.API_COMUNAS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            return _manejar_error_api(
                "La API devolvio una estructura invalida en /comunas.",
                strict,
                [],
            )
        return data
    except (requests.RequestException, ValueError) as exc:
        return _manejar_error_api(
            f"No fue posible obtener comunas desde la API: {exc}",
            strict,
            [],
        )


def leer_mapeo_estaciones() -> pd.DataFrame:
    """Lee y valida el contrato del archivo de mapeo de estaciones."""
    ruta = config.FUENTE_MAPEO_ESTACIONES
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo de mapeo de estaciones: {ruta}")

    try:
        df = pd.read_csv(ruta, encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(
            "El archivo de mapeo de estaciones debe estar codificado en UTF-8."
        ) from exc

    columnas_faltantes = [
        columna for columna in MAPEO_ESTACIONES_COLUMNS if columna not in df.columns
    ]
    if columnas_faltantes:
        raise ValueError(
            "Faltan columnas requeridas en mapeo_estaciones.csv: "
            + ", ".join(columnas_faltantes)
        )

    df = df.loc[:, MAPEO_ESTACIONES_COLUMNS].copy()
    df["codigo_estacion_raw"] = (
        df["codigo_estacion_raw"].astype(str).str.strip()
    )
    duplicados = df["codigo_estacion_raw"].duplicated(keep=False)
    if duplicados.any():
        codigos = sorted(df.loc[duplicados, "codigo_estacion_raw"].unique())
        raise ValueError(
            "El archivo de mapeo contiene codigo_estacion_raw duplicados: "
            + ", ".join(codigos)
        )

    return df


def construir_mapa_manual_estaciones(df_mapeo: pd.DataFrame) -> dict[str, str]:
    """Devuelve un mapa raw_code -> codigo_unico_api desde el CSV manual."""
    return {
        str(fila["codigo_estacion_raw"]): str(fila["codigo_unico_api"])
        for _, fila in df_mapeo.iterrows()
        if pd.notna(fila["codigo_estacion_raw"]) and pd.notna(fila["codigo_unico_api"])
    }


def construir_mapa_estaciones(estaciones: list[dict]) -> dict[str, int]:
    """Construye mapa exacto codigo -> id_estacion desde la API."""
    mapa: dict[str, int] = {}
    for estacion in estaciones:
        codigo = estacion.get("codigo_unico") or estacion.get("codigo_estacion")
        id_estacion = estacion.get("id_estacion")
        if codigo and id_estacion is not None:
            mapa[str(codigo)] = int(id_estacion)
    return mapa


def resolver_ids_estaciones_api(
    df_mapeo: pd.DataFrame,
    estaciones: list[dict],
) -> dict[str, dict]:
    """Resuelve el id_estacion API para cada codigo raw definido manualmente."""
    mapa_estaciones_api = construir_mapa_estaciones(estaciones)
    resolucion: dict[str, dict] = {}

    for _, fila in df_mapeo.iterrows():
        codigo_raw = str(fila["codigo_estacion_raw"])
        codigo_unico_api = str(fila["codigo_unico_api"])
        id_estacion = mapa_estaciones_api.get(codigo_unico_api)
        resolucion[codigo_raw] = {
            "codigo_unico_api": codigo_unico_api,
            "id_estacion": int(id_estacion) if id_estacion is not None else None,
            "comuna": fila["comuna"],
            "region": fila["region"],
            "fuente_dato": fila["fuente_dato"],
            "tipo_sensor_api": fila["tipo_sensor_api"],
        }

    return resolucion


def construir_indices_estaciones(
    estaciones: list[dict],
    comunas: list[dict],
) -> tuple[dict[str, int], dict[tuple[str, str], list[dict]]]:
    """Construye indices exactos y heuristicos para mapear estaciones."""
    mapa_exacto = construir_mapa_estaciones(estaciones)
    mapa_comunas = {
        comuna.get("id_comuna"): normalizar_comuna(comuna.get("nombre"))
        for comuna in comunas
        if comuna.get("id_comuna") is not None and comuna.get("nombre")
    }

    indice_heuristico: dict[tuple[str, str], list[dict]] = {}
    for estacion in estaciones:
        id_comuna = estacion.get("id_comuna")
        tipo = estacion.get("tipo") or estacion.get("tipo_sensor")
        id_estacion = estacion.get("id_estacion")
        codigo = estacion.get("codigo_unico") or estacion.get("codigo_estacion")
        comuna_normalizada = mapa_comunas.get(id_comuna)
        if comuna_normalizada is None or tipo is None or id_estacion is None or not codigo:
            continue

        clave = (str(comuna_normalizada), str(tipo))
        indice_heuristico.setdefault(clave, []).append(
            {
                "id_estacion": int(id_estacion),
                "codigo_unico_api": str(codigo),
                "tipo_sensor": str(tipo),
                "comuna": str(comuna_normalizada),
            }
        )
    return mapa_exacto, indice_heuristico


def _inferir_tipo_sensor(codigo_estacion: str) -> str | None:
    codigo = codigo_estacion.upper()
    if codigo.startswith("OF-") or "-OF-" in codigo or codigo.endswith("-OF"):
        return "publico_oficial"
    if codigo.startswith("ONG-") or "-ONG-" in codigo or codigo.endswith("-ONG"):
        return "sensor_comunitario_ong"
    return None


def _construir_fila_omitida(
    fila,
    codigo_unico_api,
    id_estacion,
    motivo_omision: str,
    modo_mapeo: str,
) -> dict:
    return {
        "codigo_estacion": fila["codigo_estacion"],
        "codigo_unico_api": codigo_unico_api,
        "id_estacion": id_estacion,
        "comuna": fila["comuna"],
        "region": fila["region"],
        "fuente_dato": fila["fuente_dato"],
        "fecha_hora": fila["fecha_hora"],
        "motivo_omision": motivo_omision,
        "modo_mapeo": modo_mapeo,
    }


def _tiene_clima_incompleto_api(fila) -> bool:
    return any(pd.isna(fila[columna]) for columna in CLIMA_REQUERIDO_API_COLUMNS)


def preparar_payload_bulk(
    df_mediciones_validas: pd.DataFrame,
    mapa_estaciones_api: dict[str, int],
    mapa_manual_resuelto: dict[str, dict] | None = None,
    indice_heuristico: dict[tuple[str, str], list[dict]] | None = None,
) -> tuple[list[dict], pd.DataFrame]:
    """Prepara payload para /monitoreo/bulk y separa omitidas por mapeo."""
    mapa_manual_resuelto = mapa_manual_resuelto or {}
    indice_heuristico = indice_heuristico or {}

    payload: list[dict] = []
    omitidas: list[dict] = []

    for _, fila in df_mediciones_validas.iterrows():
        codigo_estacion = str(fila["codigo_estacion"]).strip()
        comuna = normalizar_comuna(fila["comuna"])
        tipo_sensor = _inferir_tipo_sensor(codigo_estacion)

        codigo_unico_api = None
        id_estacion = mapa_estaciones_api.get(codigo_estacion)
        modo_mapeo = "exacto_api" if id_estacion is not None else "sin_mapeo"
        motivo_omision = "estacion_no_encontrada"

        if id_estacion is not None:
            codigo_unico_api = codigo_estacion
        else:
            info_manual = mapa_manual_resuelto.get(codigo_estacion)
            if info_manual is not None:
                codigo_unico_api = info_manual["codigo_unico_api"]
                modo_mapeo = "mapeo_manual_csv"
                id_estacion = info_manual["id_estacion"]
                if id_estacion is None:
                    motivo_omision = "codigo_api_no_disponible"
            elif pd.notna(comuna) and tipo_sensor is not None:
                candidatas = indice_heuristico.get((str(comuna), tipo_sensor), [])
                modo_mapeo = "heuristico_seguro"
                if len(candidatas) == 1:
                    id_estacion = candidatas[0]["id_estacion"]
                    codigo_unico_api = candidatas[0]["codigo_unico_api"]
                elif len(candidatas) > 1:
                    motivo_omision = "estacion_ambigua"
                else:
                    motivo_omision = "estacion_no_encontrada"

        if id_estacion is None:
            omitidas.append(
                _construir_fila_omitida(
                    fila=fila,
                    codigo_unico_api=codigo_unico_api,
                    id_estacion=id_estacion,
                    motivo_omision=motivo_omision,
                    modo_mapeo=modo_mapeo,
                )
            )
            continue

        if _tiene_clima_incompleto_api(fila):
            omitidas.append(
                _construir_fila_omitida(
                    fila=fila,
                    codigo_unico_api=codigo_unico_api,
                    id_estacion=id_estacion,
                    motivo_omision="clima_requerido_por_api",
                    modo_mapeo=modo_mapeo,
                )
            )
            continue

        payload.append(
            {
                "fecha_hora": _serializar_fecha(fila["fecha_hora"]),
                "id_estacion": int(id_estacion),
                "mp25": float(fila["mp25"]),
                "mp10": float(fila["mp10"]),
                "so2": float(fila["so2"]),
                "no2": float(fila["no2"]),
                "velocidad_viento": _serializar_valor(fila["velocidad_viento"]),
                "direccion_viento_grados": _serializar_valor(
                    fila["direccion_viento_grados"]
                ),
                "temperatura": _serializar_valor(fila["temperatura"]),
                "humedad": _serializar_valor(fila["humedad"]),
                "_codigo_estacion": fila["codigo_estacion"],
                "_codigo_unico_api": codigo_unico_api,
                "_comuna": fila["comuna"],
                "_region": fila["region"],
                "_fuente_dato": fila["fuente_dato"],
                "_modo_mapeo": modo_mapeo,
            }
        )

    omitidas_df = pd.DataFrame(omitidas, columns=OMITIDAS_COLUMNS)
    if omitidas_df.empty:
        omitidas_df = pd.DataFrame(columns=OMITIDAS_COLUMNS)
    return payload, omitidas_df


def obtener_mediciones_api(
    id_estacion: int,
    fecha_inicio: str,
    fecha_fin: str,
    strict: bool = False,
) -> list[dict]:
    """Obtiene mediciones existentes en la API para una estacion y rango dado."""
    registros: list[dict] = []
    offset = 0
    limit = 1000

    while True:
        params = {
            "id_estacion": id_estacion,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "limit": limit,
            "offset": offset,
        }
        try:
            response = requests.get(config.API_MONITOREO_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            return _manejar_error_api(
                f"No fue posible consultar mediciones existentes en /monitoreo: {exc}",
                strict,
                [],
            )

        if not isinstance(data, list):
            return _manejar_error_api(
                "La API devolvio una estructura invalida en /monitoreo.",
                strict,
                [],
            )

        registros.extend(data)
        if len(data) < limit:
            break
        offset += limit

    return registros


def filtrar_mediciones_existentes(
    payload: list[dict],
    strict: bool = False,
) -> tuple[list[dict], pd.DataFrame]:
    """Filtra mediciones ya presentes en la API antes del bulk."""
    if not payload:
        return [], pd.DataFrame(columns=OMITIDAS_COLUMNS)

    existentes: set[tuple[int, str]] = set()
    por_estacion: dict[int, list[dict]] = {}

    for medicion in payload:
        por_estacion.setdefault(int(medicion["id_estacion"]), []).append(medicion)

    for id_estacion, mediciones in por_estacion.items():
        fechas = [
            _normalizar_fecha_clave(medicion["fecha_hora"])
            for medicion in mediciones
            if _normalizar_fecha_clave(medicion["fecha_hora"]) is not None
        ]
        if not fechas:
            continue

        registros_api = obtener_mediciones_api(
            id_estacion=id_estacion,
            fecha_inicio=min(fechas),
            fecha_fin=max(fechas),
            strict=strict,
        )
        for registro in registros_api:
            fecha = _normalizar_fecha_clave(registro.get("fecha_hora"))
            estacion = registro.get("id_estacion")
            if fecha is not None and estacion is not None:
                existentes.add((int(estacion), fecha))

    nuevas: list[dict] = []
    omitidas: list[dict] = []
    for medicion in payload:
        clave = (
            int(medicion["id_estacion"]),
            _normalizar_fecha_clave(medicion["fecha_hora"]),
        )
        if clave in existentes:
            omitidas.append(
                {
                    "codigo_estacion": medicion["_codigo_estacion"],
                    "codigo_unico_api": medicion["_codigo_unico_api"],
                    "id_estacion": medicion["id_estacion"],
                    "comuna": medicion["_comuna"],
                    "region": medicion["_region"],
                    "fuente_dato": medicion["_fuente_dato"],
                    "fecha_hora": medicion["fecha_hora"],
                    "motivo_omision": "medicion_ya_existente",
                    "modo_mapeo": medicion["_modo_mapeo"],
                }
            )
            continue
        nuevas.append(medicion)

    omitidas_df = pd.DataFrame(omitidas, columns=OMITIDAS_COLUMNS)
    if omitidas_df.empty:
        omitidas_df = pd.DataFrame(columns=OMITIDAS_COLUMNS)
    return nuevas, omitidas_df


def guardar_payload_bulk(payload: list[dict]) -> None:
    """Guarda el payload bulk como evidencia del ETL."""
    contenido = {"mediciones": _payload_envio(payload)}
    with config.SALIDA_PAYLOAD_BULK.open("w", encoding="utf-8") as file:
        json.dump(contenido, file, ensure_ascii=False, indent=2)


def cargar_mediciones_bulk(payload: list[dict], dry_run: bool = False) -> dict:
    """Carga mediciones a la API o realiza solo dry-run."""
    payload_envio = _payload_envio(payload)
    if not payload_envio:
        return {
            "modo": "dry-run" if dry_run else "api",
            "total_preparadas": 0,
            "insertados": 0,
            "errores": 0,
            "mensaje": "No hay mediciones nuevas compatibles para enviar a la API.",
        }

    if dry_run:
        return {
            "modo": "dry-run",
            "total_preparadas": len(payload_envio),
            "insertados": 0,
            "errores": 0,
            "mensaje": "Payload preparado sin envio a API.",
        }

    try:
        response = requests.post(
            config.API_MONITOREO_BULK_URL,
            json={"mediciones": payload_envio},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict):
            data["modo"] = "api"
            data["total_preparadas"] = len(payload_envio)
            return data
        return {
            "modo": "api",
            "total_preparadas": len(payload_envio),
            "insertados": 0,
            "errores": 0,
            "mensaje": "Respuesta API sin estructura esperada.",
        }
    except requests.RequestException as exc:
        return {
            "modo": "api-error",
            "total_preparadas": len(payload_envio),
            "insertados": 0,
            "errores": len(payload_envio),
            "mensaje": f"Error al enviar mediciones a API: {exc}",
        }


def guardar_omitidas_carga(omitidas: pd.DataFrame | None = None) -> None:
    """Guarda detalle fila a fila de mediciones omitidas en la carga."""
    omitidas = omitidas if omitidas is not None else pd.DataFrame(columns=OMITIDAS_COLUMNS)
    if omitidas.empty:
        omitidas = pd.DataFrame(columns=OMITIDAS_COLUMNS)
    omitidas.to_csv(config.SALIDA_OMITIDAS_CARGA_API, index=False, encoding="utf-8")


def guardar_reporte_carga(respuesta: dict, omitidas: pd.DataFrame | None = None) -> None:
    """Guarda un reporte resumido de la carga a API."""
    omitidas = omitidas if omitidas is not None else pd.DataFrame(columns=OMITIDAS_COLUMNS)
    if omitidas.empty:
        omitidas = pd.DataFrame(columns=OMITIDAS_COLUMNS)

    detalle_errores = respuesta.get("detalle_errores", [])
    resumen = {
        "modo": respuesta.get("modo", ""),
        "total_preparadas": respuesta.get("total_preparadas", 0),
        "total_con_id_estacion": respuesta.get("total_con_id_estacion", 0),
        "omitidas_por_estacion_no_encontrada": int(
            (omitidas["motivo_omision"] == "estacion_no_encontrada").sum()
        ),
        "omitidas_por_estacion_ambigua": int(
            (omitidas["motivo_omision"] == "estacion_ambigua").sum()
        ),
        "omitidas_por_codigo_api_no_disponible": int(
            (omitidas["motivo_omision"] == "codigo_api_no_disponible").sum()
        ),
        "omitidas_por_clima_requerido_api": int(
            (omitidas["motivo_omision"] == "clima_requerido_por_api").sum()
        ),
        "omitidas_por_medicion_ya_existente": int(
            (omitidas["motivo_omision"] == "medicion_ya_existente").sum()
        ),
        "insertados": respuesta.get("insertados", 0),
        "errores": respuesta.get("errores", 0),
        "mensaje": respuesta.get("mensaje", ""),
        "modo_mapeo": respuesta.get(
            "modo_mapeo",
            "exacto_api>mapeo_manual_csv>heuristico_seguro",
        ),
        "detalle_errores": json.dumps(detalle_errores, ensure_ascii=False),
    }
    pd.DataFrame([resumen]).to_csv(
        config.SALIDA_REPORTE_CARGA_API,
        index=False,
        encoding="utf-8",
    )


def guardar_dataset_modelado(
    dry_run: bool = False,
    strict: bool = False,
) -> pd.DataFrame:
    """Guarda dataset modelado desde API o en fallback local."""
    if dry_run:
        df = pd.read_csv(config.SALIDA_MEDICIONES_VALIDAS)
        df.to_csv(config.SALIDA_DATASET_MODELADO, index=False, encoding="utf-8")
        return df

    try:
        response = requests.get(config.API_DATASET_MODELADO_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise ValueError("La API devolvio una estructura invalida.")
        df = pd.DataFrame(data)
        df.to_csv(config.SALIDA_DATASET_MODELADO, index=False, encoding="utf-8")
        return df
    except (requests.RequestException, ValueError) as exc:
        if strict:
            raise RuntimeError(
                f"No fue posible obtener dataset_modelado desde la API: {exc}"
            ) from exc
        return guardar_dataset_modelado(dry_run=True, strict=False)
