from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    AnalyticsComunaCritica,
    AnalyticsEvolucionMp25,
    AnalyticsIcaPorComuna,
    AnalyticsMp25PorComuna,
    AnalyticsRankingSensor,
    AnalyticsResumen,
    DatasetModelado,
)
from app.services.analytics_service import (
    obtener_comunas_criticas,
    obtener_dataset_modelado,
    obtener_evolucion_mp25,
    obtener_ica_por_comuna,
    obtener_mp25_por_comuna,
    obtener_ranking_sensores,
    obtener_resumen_general,
)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/resumen-general", response_model=AnalyticsResumen)
def resumen_general(db: Session = Depends(get_db)):
    try:
        return AnalyticsResumen(**obtener_resumen_general(db))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar el resumen general.",
        ) from exc


@router.get("/mp25-por-comuna", response_model=list[AnalyticsMp25PorComuna])
def mp25_por_comuna(
    region: str | None = Query(default=None),
    fecha_inicio: datetime | None = Query(default=None),
    fecha_fin: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        filas = obtener_mp25_por_comuna(
            db,
            region=region,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return [AnalyticsMp25PorComuna(**fila) for fila in filas]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar MP2.5 por comuna.",
        ) from exc


@router.get("/comunas-criticas", response_model=list[AnalyticsComunaCritica])
def comunas_criticas(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        filas = obtener_comunas_criticas(db, limit=limit)
        return [AnalyticsComunaCritica(**fila) for fila in filas]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar comunas criticas.",
        ) from exc


@router.get("/evolucion-mp25", response_model=list[AnalyticsEvolucionMp25])
def evolucion_mp25(
    id_comuna: int | None = Query(default=None),
    region: str | None = Query(default=None),
    fecha_inicio: datetime | None = Query(default=None),
    fecha_fin: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        filas = obtener_evolucion_mp25(
            db,
            id_comuna=id_comuna,
            region=region,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return [AnalyticsEvolucionMp25(**fila) for fila in filas]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar la evolucion de MP2.5.",
        ) from exc


@router.get("/ica-por-comuna", response_model=list[AnalyticsIcaPorComuna])
def ica_por_comuna(
    region: str | None = Query(default=None),
    fecha_inicio: datetime | None = Query(default=None),
    fecha_fin: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        filas = obtener_ica_por_comuna(
            db,
            region=region,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )
        return [AnalyticsIcaPorComuna(**fila) for fila in filas]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar ICA por comuna.",
        ) from exc


@router.get("/ranking-sensores", response_model=list[AnalyticsRankingSensor])
def ranking_sensores(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    try:
        filas = obtener_ranking_sensores(db, limit=limit)
        return [AnalyticsRankingSensor(**fila) for fila in filas]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar ranking de sensores.",
        ) from exc


@router.get("/dataset-modelado", response_model=list[DatasetModelado])
def dataset_modelado(
    region: str | None = Query(default=None),
    id_comuna: int | None = Query(default=None),
    fecha_inicio: datetime | None = Query(default=None),
    fecha_fin: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    try:
        filas = obtener_dataset_modelado(
            db,
            region=region,
            id_comuna=id_comuna,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            limit=limit,
            offset=offset,
        )
        return [DatasetModelado(**fila) for fila in filas]
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=500,
            detail="Error al consultar dataset para modelado.",
        ) from exc
