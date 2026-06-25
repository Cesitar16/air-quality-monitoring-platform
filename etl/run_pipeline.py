"""Pipeline entrypoint for the ETL workflow."""

import argparse
import os
from pathlib import Path
import sys

import pandas as pd

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl.config import (  # noqa: E402
    FUENTE_MAPEO_ESTACIONES,
    ROOT_DIR,
    SALIDA_CLIMA_LIMPIO,
    SALIDA_DATASET_MODELADO,
    SALIDA_ERRORES_ETL,
    SALIDA_INDUSTRIAS_LIMPIAS,
    SALIDA_MEDICIONES_LIMPIAS,
    SALIDA_MEDICIONES_VALIDAS,
    SALIDA_OMITIDAS_CARGA_API,
    SALIDA_PAYLOAD_BULK,
    SALIDA_REPORTE_CARGA_API,
    crear_directorios_base,
)
from etl.extract import extraer_todas_las_fuentes  # noqa: E402
from etl.load import (  # noqa: E402
    cargar_mediciones_bulk,
    construir_indices_estaciones,
    filtrar_mediciones_existentes,
    guardar_dataset_modelado,
    guardar_omitidas_carga,
    guardar_payload_bulk,
    guardar_reporte_carga,
    leer_mapeo_estaciones,
    obtener_comunas_api,
    obtener_estaciones_api,
    preparar_payload_bulk,
    resolver_ids_estaciones_api,
    verificar_api_disponible,
)
from etl.transform import transformar_fuentes  # noqa: E402
from etl.validate import validar_mediciones  # noqa: E402


def _ruta_relativa(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR)).replace("\\", "/")
    except ValueError:
        return str(path)


def _parse_args(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Pipeline ETL de calidad del aire")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Prepara carga sin enviar datos a la API.",
    )
    parser.add_argument(
        "--load-api",
        action="store_true",
        help="Intenta cargar datos reales a la API.",
    )
    if argv is None:
        argv = []
    return parser.parse_args(argv)


def _resolver_modo_dry_run(args) -> bool:
    env_value = os.getenv("ETL_DRY_RUN", "").strip().lower()
    dry_run_env = env_value in {"1", "true", "yes", "on"}

    if args.load_api:
        return False
    if args.dry_run:
        return True
    return dry_run_env or True


def _guardar_salidas_transformacion(fuentes_transformadas: dict[str, pd.DataFrame]) -> None:
    fuentes_transformadas["mediciones_limpias"].to_csv(
        SALIDA_MEDICIONES_LIMPIAS,
        index=False,
        encoding="utf-8",
    )
    fuentes_transformadas["industrias_limpias"].to_csv(
        SALIDA_INDUSTRIAS_LIMPIAS,
        index=False,
        encoding="utf-8",
    )
    fuentes_transformadas["clima_limpio"].to_csv(
        SALIDA_CLIMA_LIMPIO,
        index=False,
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    dry_run = _resolver_modo_dry_run(args)

    print("[ETL] Inicializando pipeline de calidad del aire...")
    crear_directorios_base()
    print("[ETL] Directorios base verificados.")
    print("[ETL] Extrayendo fuentes raw...")
    fuentes = extraer_todas_las_fuentes()
    for nombre_fuente, dataframe in fuentes.items():
        print(f"[ETL] {nombre_fuente}: {len(dataframe)} filas")

    print("[ETL] Transformando fuentes...")
    fuentes_transformadas = transformar_fuentes(fuentes)
    for nombre_fuente, dataframe in fuentes_transformadas.items():
        print(f"[ETL] {nombre_fuente}: {len(dataframe)} filas")
    _guardar_salidas_transformacion(fuentes_transformadas)

    print(f"[ETL] Archivo generado: {_ruta_relativa(SALIDA_MEDICIONES_LIMPIAS)}")
    print(f"[ETL] Archivo generado: {_ruta_relativa(SALIDA_INDUSTRIAS_LIMPIAS)}")
    print(f"[ETL] Archivo generado: {_ruta_relativa(SALIDA_CLIMA_LIMPIO)}")

    print("[ETL] Validando mediciones...")
    mediciones_validas, errores_etl = validar_mediciones(
        fuentes_transformadas["mediciones_limpias"]
    )
    mediciones_validas.to_csv(
        SALIDA_MEDICIONES_VALIDAS,
        index=False,
        encoding="utf-8",
    )
    errores_etl.to_csv(
        SALIDA_ERRORES_ETL,
        index=False,
        encoding="utf-8",
    )

    print(f"[ETL] mediciones_validas: {len(mediciones_validas)} filas")
    print(f"[ETL] errores_etl: {len(errores_etl)} filas")
    print(f"[ETL] Archivo generado: {_ruta_relativa(SALIDA_MEDICIONES_VALIDAS)}")
    print(f"[ETL] Archivo generado: {_ruta_relativa(SALIDA_ERRORES_ETL)}")

    print("[ETL] Preparando carga a API...")
    df_mapeo_estaciones = leer_mapeo_estaciones()
    print(f"[ETL] Mapeo de estaciones verificado: {_ruta_relativa(FUENTE_MAPEO_ESTACIONES)}")

    estaciones: list[dict] = []
    comunas: list[dict] = []
    mapa_manual_resuelto: dict[str, dict] = {}
    if dry_run:
        print("[ETL] Modo dry-run activo: no se enviaran datos a la API.")
    else:
        print("[ETL] Verificando API...")
        if not verificar_api_disponible():
            raise RuntimeError(
                "La API no esta disponible para --load-api. Levanta Docker y valida /health."
            )
        print("[ETL] API disponible.")
        estaciones = obtener_estaciones_api(strict=True)
        comunas = obtener_comunas_api(strict=True)
        mapa_manual_resuelto = resolver_ids_estaciones_api(df_mapeo_estaciones, estaciones)

    mapa_estaciones_api, indice_heuristico = construir_indices_estaciones(estaciones, comunas)
    if dry_run and estaciones:
        mapa_manual_resuelto = resolver_ids_estaciones_api(df_mapeo_estaciones, estaciones)

    payload_preparado, omitidas_mapeo = preparar_payload_bulk(
        mediciones_validas,
        mapa_estaciones_api,
        mapa_manual_resuelto=mapa_manual_resuelto,
        indice_heuristico=indice_heuristico,
    )
    omitidas_clima = int(
        (omitidas_mapeo["motivo_omision"] == "clima_requerido_por_api").sum()
    )

    payload_final = payload_preparado
    omitidas_existentes = pd.DataFrame(columns=omitidas_mapeo.columns)
    if not dry_run:
        payload_final, omitidas_existentes = filtrar_mediciones_existentes(
            payload_preparado,
            strict=True,
        )

    dataframes_omitidas = [
        dataframe for dataframe in (omitidas_mapeo, omitidas_existentes) if not dataframe.empty
    ]
    if dataframes_omitidas:
        omitidas_total = pd.concat(dataframes_omitidas, ignore_index=True)
    else:
        omitidas_total = pd.DataFrame(columns=omitidas_mapeo.columns)

    guardar_payload_bulk(payload_final)
    guardar_omitidas_carga(omitidas_total)

    respuesta_carga = cargar_mediciones_bulk(payload_final, dry_run=dry_run)
    if not dry_run and respuesta_carga.get("modo") == "api-error":
        raise RuntimeError(respuesta_carga.get("mensaje", "Fallo la carga bulk a la API."))

    respuesta_carga["total_con_id_estacion"] = (
        len(payload_final) + len(omitidas_existentes) + omitidas_clima
    )
    respuesta_carga["modo_mapeo"] = "exacto_api>mapeo_manual_csv>heuristico_seguro"
    guardar_reporte_carga(respuesta_carga, omitidas=omitidas_total)

    dataset_modelado = guardar_dataset_modelado(dry_run=dry_run, strict=not dry_run)

    print(
        "[ETL] "
        f"Mediciones con id_estacion: {respuesta_carga['total_con_id_estacion']}; "
        f"compatibles con schema API: {len(payload_preparado)}; "
        f"listas para envio: {len(payload_final)}; "
        f"omitidas: {len(omitidas_total)}"
    )
    print(f"[ETL] Payload generado: {_ruta_relativa(SALIDA_PAYLOAD_BULK)}")
    print(f"[ETL] Omitidas generadas: {_ruta_relativa(SALIDA_OMITIDAS_CARGA_API)}")
    print(f"[ETL] Reporte generado: {_ruta_relativa(SALIDA_REPORTE_CARGA_API)}")
    print(f"[ETL] Dataset modelado generado: {_ruta_relativa(SALIDA_DATASET_MODELADO)}")

    if dry_run:
        print("[ETL] Fase 6 completada: carga preparada.")
    else:
        print(
            "[ETL] "
            f"Respuesta API: insertados={respuesta_carga.get('insertados', 0)}, "
            f"errores={respuesta_carga.get('errores', 0)}"
        )
        print(f"[ETL] dataset_modelado: {len(dataset_modelado)} filas")
        print("[ETL] Fase 6 completada: carga API ejecutada.")


if __name__ == "__main__":
    main(sys.argv[1:])
