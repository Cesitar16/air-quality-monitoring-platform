from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EstacionSensor, MonitoreoAmbiental
from app.schemas import MonitoreoCreate, MonitoreoDetalleResponse

router = APIRouter(tags=["Monitoreo"])


MONITOREO_SELECT = """
    SELECT
        m.id_monitoreo,
        m.fecha_hora,
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


@router.get("/monitoreo", response_model=list[MonitoreoDetalleResponse])
def listar_monitoreo(
    comuna: str | None = Query(default=None),
    region: str | None = Query(default=None),
    fecha_inicio: datetime | None = Query(default=None),
    fecha_fin: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = MONITOREO_SELECT + "\nWHERE 1 = 1"
    params: dict[str, object] = {"limit_value": limit}

    if comuna:
        query += " AND c.nombre ILIKE :comuna"
        params["comuna"] = f"%{comuna}%"
    if region:
        query += " AND c.region = :region"
        params["region"] = region
    if fecha_inicio:
        query += " AND m.fecha_hora >= :fecha_inicio"
        params["fecha_inicio"] = fecha_inicio
    if fecha_fin:
        query += " AND m.fecha_hora <= :fecha_fin"
        params["fecha_fin"] = fecha_fin

    query += " ORDER BY m.fecha_hora DESC LIMIT :limit_value"

    try:
        rows = db.execute(text(query), params).mappings().all()
        return [MonitoreoDetalleResponse(**row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar monitoreo.") from exc


@router.get("/monitoreo/{id_monitoreo}", response_model=MonitoreoDetalleResponse)
def obtener_monitoreo(id_monitoreo: int, db: Session = Depends(get_db)):
    query = text(MONITOREO_SELECT + "\nWHERE m.id_monitoreo = :id_monitoreo")

    try:
        row = db.execute(query, {"id_monitoreo": id_monitoreo}).mappings().first()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar el monitoreo.") from exc

    if row is None:
        raise HTTPException(status_code=404, detail="Monitoreo no encontrado.")
    return MonitoreoDetalleResponse(**row)


@router.post("/monitoreo", response_model=MonitoreoDetalleResponse, status_code=status.HTTP_201_CREATED)
def crear_monitoreo(payload: MonitoreoCreate, db: Session = Depends(get_db)):
    estacion = (
        db.query(EstacionSensor)
        .filter(EstacionSensor.id_estacion == payload.id_estacion)
        .first()
    )
    if estacion is None:
        raise HTTPException(status_code=404, detail="La estacion indicada no existe.")

    nuevo_monitoreo = MonitoreoAmbiental(**payload.model_dump())

    try:
        db.add(nuevo_monitoreo)
        db.commit()
        db.refresh(nuevo_monitoreo)
        row = db.execute(
            text(MONITOREO_SELECT + "\nWHERE m.id_monitoreo = :id_monitoreo"),
            {"id_monitoreo": nuevo_monitoreo.id_monitoreo},
        ).mappings().first()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se pudo insertar el monitoreo. Verifica fecha_hora e id_estacion.",
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error al crear el monitoreo.") from exc

    if row is None:
        raise HTTPException(
            status_code=500,
            detail="El monitoreo se creo, pero no pudo recuperarse.",
        )
    return MonitoreoDetalleResponse(**row)
