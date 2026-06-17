from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import EstacionSensor
from app.schemas import EstacionResponse

router = APIRouter(prefix="/estaciones", tags=["Estaciones"])


@router.get("", response_model=list[EstacionResponse])
def listar_estaciones(db: Session = Depends(get_db)):
    try:
        return db.query(EstacionSensor).order_by(EstacionSensor.id_estacion).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar estaciones.") from exc


@router.get("/{id_estacion}", response_model=EstacionResponse)
def obtener_estacion(id_estacion: int, db: Session = Depends(get_db)):
    try:
        estacion = (
            db.query(EstacionSensor)
            .filter(EstacionSensor.id_estacion == id_estacion)
            .first()
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar la estación.") from exc

    if estacion is None:
        raise HTTPException(status_code=404, detail="Estación no encontrada.")
    return estacion
