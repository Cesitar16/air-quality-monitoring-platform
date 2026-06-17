from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Comuna
from app.schemas import ComunaResponse

router = APIRouter(prefix="/comunas", tags=["Comunas"])


@router.get("", response_model=list[ComunaResponse])
def listar_comunas(db: Session = Depends(get_db)):
    try:
        return db.query(Comuna).order_by(Comuna.id_comuna).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar comunas.") from exc


@router.get("/{id_comuna}", response_model=ComunaResponse)
def obtener_comuna(id_comuna: int, db: Session = Depends(get_db)):
    try:
        comuna = db.query(Comuna).filter(Comuna.id_comuna == id_comuna).first()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar la comuna.") from exc

    if comuna is None:
        raise HTTPException(status_code=404, detail="Comuna no encontrada.")
    return comuna
