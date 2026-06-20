from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.services.calidad_aire_service import clasificar_calidad_aire_mp25


BASE_ANALYTICS_JOIN = """
    FROM monitoreo_ambiental m
    INNER JOIN estaciones_sensores e
        ON e.id_estacion = m.id_estacion
    INNER JOIN comunas c
        ON c.id_comuna = e.id_comuna
"""

BASE_DATASET_JOIN = """
    FROM monitoreo_ambiental m
    INNER JOIN estaciones_sensores e
        ON e.id_estacion = m.id_estacion
    INNER JOIN comunas c
        ON c.id_comuna = e.id_comuna
    -- Se agrega una subconsulta agregada por comuna para evitar duplicar
    -- filas de monitoreo cuando una comuna tiene varias industrias.
    LEFT JOIN (
        SELECT
            id_comuna,
            MAX(emision_maxima_permitida) AS emision_maxima_permitida
        FROM industrias_fuentes
        GROUP BY id_comuna
    ) i
        ON i.id_comuna = c.id_comuna
"""


def construir_filtros_sql(
    *,
    region: str | None = None,
    id_comuna: int | None = None,
    id_estacion: int | None = None,
    fecha_inicio: datetime | None = None,
    fecha_fin: datetime | None = None,
    tipo_sensor: str | None = None,
    mp25_min: float | None = None,
    mp25_max: float | None = None,
    comuna: str | None = None,
) -> tuple[str, dict[str, object]]:
    filtros = ["WHERE 1 = 1"]
    params: dict[str, object] = {}

    if region:
        filtros.append("AND c.region = :region")
        params["region"] = region
    if id_comuna is not None:
        filtros.append("AND c.id_comuna = :id_comuna")
        params["id_comuna"] = id_comuna
    if id_estacion is not None:
        filtros.append("AND e.id_estacion = :id_estacion")
        params["id_estacion"] = id_estacion
    if fecha_inicio:
        filtros.append("AND m.fecha_hora >= :fecha_inicio")
        params["fecha_inicio"] = fecha_inicio
    if fecha_fin:
        filtros.append("AND m.fecha_hora <= :fecha_fin")
        params["fecha_fin"] = fecha_fin
    if tipo_sensor:
        filtros.append("AND e.tipo = :tipo_sensor")
        params["tipo_sensor"] = tipo_sensor
    if mp25_min is not None:
        filtros.append("AND m.mp25 >= :mp25_min")
        params["mp25_min"] = mp25_min
    if mp25_max is not None:
        filtros.append("AND m.mp25 <= :mp25_max")
        params["mp25_max"] = mp25_max
    if comuna:
        filtros.append("AND LOWER(c.nombre) LIKE :comuna")
        params["comuna"] = f"%{comuna.lower()}%"

    return "\n".join(filtros), params


def ejecutar_mappings(db: Session, query: str, params: dict[str, object] | None = None):
    try:
        return db.execute(text(query), params or {}).mappings().all()
    except SQLAlchemyError as exc:
        raise exc


def obtener_resumen_general(db: Session) -> dict[str, object]:
    resumen_query = """
        SELECT
            (SELECT COUNT(*) FROM comunas) AS total_comunas,
            (SELECT COUNT(*) FROM estaciones_sensores) AS total_estaciones,
            (SELECT COUNT(*) FROM industrias_fuentes) AS total_industrias,
            (SELECT COUNT(*) FROM monitoreo_ambiental) AS total_mediciones,
            COALESCE((SELECT ROUND(AVG(mp25), 2) FROM monitoreo_ambiental), 0) AS mp25_promedio,
            COALESCE((SELECT ROUND(MAX(mp25), 2) FROM monitoreo_ambiental), 0) AS mp25_maximo,
            (
                SELECT c.nombre
                FROM monitoreo_ambiental m
                INNER JOIN estaciones_sensores e ON e.id_estacion = m.id_estacion
                INNER JOIN comunas c ON c.id_comuna = e.id_comuna
                GROUP BY c.id_comuna, c.nombre
                ORDER BY AVG(m.mp25) DESC
                LIMIT 1
            ) AS comuna_mas_critica
    """
    filas = ejecutar_mappings(db, resumen_query)
    return dict(filas[0]) if filas else {}


def obtener_mp25_por_comuna(
    db: Session,
    *,
    region: str | None = None,
    fecha_inicio: datetime | None = None,
    fecha_fin: datetime | None = None,
) -> list[dict[str, object]]:
    filtros, params = construir_filtros_sql(
        region=region,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    query = f"""
        SELECT
            c.nombre AS comuna,
            c.region,
            ROUND(AVG(m.mp25), 2) AS mp25_promedio,
            COUNT(*) AS cantidad_mediciones
        {BASE_ANALYTICS_JOIN}
        {filtros}
        GROUP BY c.id_comuna, c.nombre, c.region
        ORDER BY AVG(m.mp25) DESC, c.nombre
    """
    return [dict(row) for row in ejecutar_mappings(db, query, params)]


def obtener_comunas_criticas(
    db: Session,
    *,
    limit: int = 10,
) -> list[dict[str, object]]:
    query = f"""
        SELECT
            c.nombre AS comuna,
            c.region,
            ROUND(AVG(m.mp25), 2) AS mp25_promedio,
            ROUND(MAX(m.mp25), 2) AS mp25_maximo
        {BASE_ANALYTICS_JOIN}
        GROUP BY c.id_comuna, c.nombre, c.region
        ORDER BY AVG(m.mp25) DESC, MAX(m.mp25) DESC
        LIMIT :limit_value
    """
    filas = ejecutar_mappings(db, query, {"limit_value": limit})
    resultado: list[dict[str, object]] = []
    for fila in filas:
        fila_dict = dict(fila)
        fila_dict["categoria"] = clasificar_calidad_aire_mp25(
            float(fila_dict["mp25_promedio"])
        )["categoria"]
        resultado.append(fila_dict)
    return resultado


def obtener_evolucion_mp25(
    db: Session,
    *,
    id_comuna: int | None = None,
    region: str | None = None,
    fecha_inicio: datetime | None = None,
    fecha_fin: datetime | None = None,
) -> list[dict[str, object]]:
    filtros, params = construir_filtros_sql(
        id_comuna=id_comuna,
        region=region,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    query = f"""
        SELECT
            DATE(m.fecha_hora) AS fecha,
            c.nombre AS comuna,
            ROUND(AVG(m.mp25), 2) AS mp25_promedio
        {BASE_ANALYTICS_JOIN}
        {filtros}
        GROUP BY DATE(m.fecha_hora), c.id_comuna, c.nombre
        ORDER BY DATE(m.fecha_hora), c.nombre
    """
    return [dict(row) for row in ejecutar_mappings(db, query, params)]


def obtener_ica_por_comuna(
    db: Session,
    *,
    region: str | None = None,
    fecha_inicio: datetime | None = None,
    fecha_fin: datetime | None = None,
) -> list[dict[str, object]]:
    filas = obtener_mp25_por_comuna(
        db,
        region=region,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    resultado: list[dict[str, object]] = []
    for fila in filas:
        clasificacion = clasificar_calidad_aire_mp25(float(fila["mp25_promedio"]))
        resultado.append(
            {
                "comuna": fila["comuna"],
                "region": fila["region"],
                "mp25_promedio": fila["mp25_promedio"],
                "categoria": clasificacion["categoria"],
                "mensaje_ciudadano": clasificacion["mensaje_ciudadano"],
                "color_referencial": clasificacion["color_referencial"],
            }
        )
    return resultado


def obtener_ranking_sensores(db: Session, *, limit: int = 20) -> list[dict[str, object]]:
    query = f"""
        SELECT
            e.id_estacion,
            e.codigo_unico AS codigo_estacion,
            e.tipo AS tipo_sensor,
            c.nombre AS comuna,
            ROUND(AVG(m.mp25), 2) AS mp25_promedio,
            COUNT(*) AS cantidad_mediciones
        {BASE_ANALYTICS_JOIN}
        GROUP BY e.id_estacion, e.codigo_unico, e.tipo, c.nombre
        ORDER BY AVG(m.mp25) DESC, COUNT(*) DESC
        LIMIT :limit_value
    """
    return [dict(row) for row in ejecutar_mappings(db, query, {"limit_value": limit})]


def obtener_dataset_modelado(
    db: Session,
    *,
    region: str | None = None,
    id_comuna: int | None = None,
    fecha_inicio: datetime | None = None,
    fecha_fin: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, object]]:
    filtros, params = construir_filtros_sql(
        region=region,
        id_comuna=id_comuna,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
    )
    params["limit_value"] = limit
    params["offset_value"] = offset
    query = f"""
        SELECT
            m.fecha_hora,
            c.nombre AS comuna,
            c.region,
            e.codigo_unico AS codigo_estacion,
            e.tipo AS tipo_sensor,
            m.mp25,
            m.mp10,
            m.so2,
            m.no2,
            m.velocidad_viento,
            m.direccion_viento_grados,
            m.temperatura,
            m.humedad,
            c.indice_vulnerabilidad_respiratoria,
            i.emision_maxima_permitida
        {BASE_DATASET_JOIN}
        {filtros}
        ORDER BY m.fecha_hora DESC
        LIMIT :limit_value OFFSET :offset_value
    """
    filas = ejecutar_mappings(db, query, params)
    dataset: list[dict[str, object]] = []
    for fila in filas:
        fila_dict = dict(fila)
        fila_dict["categoria_ica"] = clasificar_calidad_aire_mp25(
            float(fila_dict["mp25"])
        )["categoria"]
        dataset.append(fila_dict)
    return dataset
