from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EstacionSensor, MonitoreoAmbiental
from app.schemas import (
    MonitoreoBulkCreate,
    MonitoreoBulkError,
    MonitoreoBulkResponse,
    MonitoreoCreate,
    MonitoreoDetalleResponse,
)
from app.services.analytics_service import construir_filtros_sql

router = APIRouter(tags=["Monitoreo"])


MONITOREO_SELECT = """
    SELECT
        m.id_monitoreo,
        m.fecha_hora,
        e.id_estacion,
        c.id_comuna,
        c.nombre AS comuna,
        c.region,
        c.poblacion_estimada,
        c.indice_vulnerabilidad_respiratoria,
        e.codigo_unico,
        e.tipo,
        e.latitud,
        e.longitud,
        m.mp25,
        m.mp10,
        m.so2,
        m.no2,
        m.velocidad_viento,
        m.direccion_viento_grados,
        m.temperatura,
        m.humedad
    FROM monitoreo_ambiental m
    INNER JOIN estaciones_sensores e
        ON e.id_estacion = m.id_estacion
    INNER JOIN comunas c
        ON c.id_comuna = e.id_comuna
"""


def _obtener_detalle_monitoreo(db: Session, id_monitoreo: int):
    query = text(MONITOREO_SELECT + "\nWHERE m.id_monitoreo = :id_monitoreo")
    return db.execute(query, {"id_monitoreo": id_monitoreo}).mappings().first()


def _mensaje_error_validacion(exc: ValidationError) -> str:
    mensajes = []
    for error in exc.errors():
        campo = ".".join(str(item) for item in error["loc"])
        mensajes.append(f"{campo}: {error['msg']}")
    return "; ".join(mensajes)


def _mensaje_error_integridad(exc: IntegrityError) -> str:
    mensaje = str(exc.orig).lower()
    if "unique" in mensaje or "uq_monitoreo_ambiental_estacion_fecha" in mensaje:
        return "Ya existe una medicion para esa estacion y fecha_hora."
    return "No se pudo insertar el monitoreo por una restriccion de base de datos."


@router.get("/monitoreo", response_model=list[MonitoreoDetalleResponse])
def listar_monitoreo(
    comuna: str | None = Query(default=None),
    id_estacion: int | None = Query(default=None),
    id_comuna: int | None = Query(default=None),
    region: str | None = Query(default=None),
    fecha_inicio: datetime | None = Query(default=None),
    fecha_fin: datetime | None = Query(default=None),
    mp25_min: float | None = Query(default=None, ge=0),
    mp25_max: float | None = Query(default=None, ge=0),
    tipo_sensor: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    filtros_sql, params = construir_filtros_sql(
        comuna=comuna,
        id_estacion=id_estacion,
        id_comuna=id_comuna,
        region=region,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        mp25_min=mp25_min,
        mp25_max=mp25_max,
        tipo_sensor=tipo_sensor,
    )
    params["limit_value"] = limit
    params["offset_value"] = offset
    query = (
        MONITOREO_SELECT
        + "\n"
        + filtros_sql
        + "\nORDER BY m.fecha_hora DESC LIMIT :limit_value OFFSET :offset_value"
    )

    try:
        rows = db.execute(text(query), params).mappings().all()
        return [MonitoreoDetalleResponse(**row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar monitoreo.") from exc


@router.get("/monitoreo/{id_monitoreo}", response_model=MonitoreoDetalleResponse)
def obtener_monitoreo(id_monitoreo: int, db: Session = Depends(get_db)):
    try:
        row = _obtener_detalle_monitoreo(db, id_monitoreo)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar el monitoreo.") from exc

    if row is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe un monitoreo con id_monitoreo={id_monitoreo}",
        )
    return MonitoreoDetalleResponse(**row)


@router.post("/monitoreo", response_model=MonitoreoDetalleResponse, status_code=status.HTTP_201_CREATED)
def crear_monitoreo(payload: MonitoreoCreate, db: Session = Depends(get_db)):
    estacion = (
        db.query(EstacionSensor)
        .filter(EstacionSensor.id_estacion == payload.id_estacion)
        .first()
    )
    if estacion is None:
        raise HTTPException(
            status_code=404,
            detail=f"No existe una estacion con id_estacion={payload.id_estacion}",
        )

    nuevo_monitoreo = MonitoreoAmbiental(**payload.model_dump())

    try:
        db.add(nuevo_monitoreo)
        db.commit()
        db.refresh(nuevo_monitoreo)
        row = _obtener_detalle_monitoreo(db, nuevo_monitoreo.id_monitoreo)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=_mensaje_error_integridad(exc)) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el monitoreo.") from exc

    if row is None:
        raise HTTPException(
            status_code=500,
            detail="El monitoreo se creo, pero no pudo recuperarse.",
        )
    return MonitoreoDetalleResponse(**row)


@router.post("/monitoreo/bulk", response_model=MonitoreoBulkResponse, status_code=status.HTTP_201_CREATED)
def crear_monitoreo_bulk(payload: MonitoreoBulkCreate, db: Session = Depends(get_db)):
    insertados = 0
    detalle_errores: list[MonitoreoBulkError] = []

    for indice, medicion_raw in enumerate(payload.mediciones):
        try:
            medicion = MonitoreoCreate.model_validate(medicion_raw)
        except ValidationError as exc:
            detalle_errores.append(
                MonitoreoBulkError(indice=indice, motivo=_mensaje_error_validacion(exc))
            )
            continue

        estacion = (
            db.query(EstacionSensor)
            .filter(EstacionSensor.id_estacion == medicion.id_estacion)
            .first()
        )
        if estacion is None:
            detalle_errores.append(
                MonitoreoBulkError(
                    indice=indice,
                    motivo=f"No existe estacion con id_estacion={medicion.id_estacion}",
                )
            )
            continue

        try:
            nuevo_monitoreo = MonitoreoAmbiental(**medicion.model_dump())
            db.add(nuevo_monitoreo)
            db.commit()
            insertados += 1
        except IntegrityError as exc:
            db.rollback()
            detalle_errores.append(
                MonitoreoBulkError(indice=indice, motivo=_mensaje_error_integridad(exc))
            )
        except SQLAlchemyError:
            db.rollback()
            detalle_errores.append(
                MonitoreoBulkError(
                    indice=indice,
                    motivo="Error interno al insertar la medicion.",
                )
            )

    return MonitoreoBulkResponse(
        insertados=insertados,
        errores=len(detalle_errores),
        detalle_errores=detalle_errores,
    )
