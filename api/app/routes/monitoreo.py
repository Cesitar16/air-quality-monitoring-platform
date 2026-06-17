from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EstacionSensor, MonitoreoAmbiental
from app.schemas import (
    DatasetMLResponse,
    MonitoreoCreate,
    MonitoreoDetalleResponse,
    ResumenComunaResponse,
)

router = APIRouter(tags=["Monitoreo"])


@router.get("/monitoreo", response_model=list[MonitoreoDetalleResponse])
def listar_monitoreo(
    comuna: str | None = Query(default=None),
    region: str | None = Query(default=None),
    nivel_riesgo: str | None = Query(default=None),
    fecha_inicio: datetime | None = Query(default=None),
    fecha_fin: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    query = """
        SELECT *
        FROM vw_monitoreo_detalle
        WHERE 1 = 1
    """
    params: dict[str, object] = {"limit_value": limit}

    if comuna:
        query += " AND comuna ILIKE :comuna"
        params["comuna"] = f"%{comuna}%"
    if region:
        query += " AND region = :region"
        params["region"] = region
    if nivel_riesgo:
        query += " AND nivel_riesgo = :nivel_riesgo"
        params["nivel_riesgo"] = nivel_riesgo
    if fecha_inicio:
        query += " AND fecha_hora >= :fecha_inicio"
        params["fecha_inicio"] = fecha_inicio
    if fecha_fin:
        query += " AND fecha_hora <= :fecha_fin"
        params["fecha_fin"] = fecha_fin

    query += " ORDER BY fecha_hora DESC LIMIT :limit_value"

    try:
        rows = db.execute(text(query), params).mappings().all()
        return [MonitoreoDetalleResponse(**row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar monitoreo.") from exc


@router.get("/monitoreo/{id_monitoreo}", response_model=MonitoreoDetalleResponse)
def obtener_monitoreo(id_monitoreo: int, db: Session = Depends(get_db)):
    query = text(
        """
        SELECT *
        FROM vw_monitoreo_detalle
        WHERE id_monitoreo = :id_monitoreo
        """
    )

    try:
        row = db.execute(query, {"id_monitoreo": id_monitoreo}).mappings().first()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar el monitoreo.") from exc

    if row is None:
        raise HTTPException(status_code=404, detail="Monitoreo no encontrado.")
    return MonitoreoDetalleResponse(**row)


@router.post("/monitoreo", response_model=MonitoreoDetalleResponse, status_code=status.HTTP_201_CREATED)
def crear_monitoreo(payload: MonitoreoCreate, db: Session = Depends(get_db)):
    estacion = db.query(EstacionSensor).filter(EstacionSensor.id_estacion == payload.id_estacion).first()
    if estacion is None:
        raise HTTPException(status_code=404, detail="La estación indicada no existe.")

    nuevo_monitoreo = MonitoreoAmbiental(**payload.model_dump())

    try:
        db.add(nuevo_monitoreo)
        db.commit()
        db.refresh(nuevo_monitoreo)

        row = db.execute(
            text(
                """
                SELECT *
                FROM vw_monitoreo_detalle
                WHERE id_monitoreo = :id_monitoreo
                """
            ),
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
        raise HTTPException(status_code=500, detail="El monitoreo se creó, pero no pudo recuperarse.")
    return MonitoreoDetalleResponse(**row)


@router.get("/resumen/comunas", response_model=list[ResumenComunaResponse])
def resumen_comunas(db: Session = Depends(get_db)):
    try:
        rows = db.execute(
            text(
                """
                SELECT *
                FROM vw_resumen_comuna
                ORDER BY comuna
                """
            )
        ).mappings().all()
        return [ResumenComunaResponse(**row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar el resumen por comunas.") from exc


@router.get("/dataset/ml", response_model=list[DatasetMLResponse])
def dataset_ml(
    limit: int = Query(default=500, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    try:
        rows = db.execute(
            text(
                """
                SELECT *
                FROM vw_dataset_ml
                ORDER BY id_monitoreo
                LIMIT :limit_value
                """
            ),
            {"limit_value": limit},
        ).mappings().all()
        return [DatasetMLResponse(**row) for row in rows]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar el dataset ML.") from exc
