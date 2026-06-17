from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import IndustriaFuente
from app.schemas import IndustriaResponse

router = APIRouter(prefix="/industrias", tags=["Industrias"])


@router.get("", response_model=list[IndustriaResponse])
def listar_industrias(db: Session = Depends(get_db)):
    try:
        return db.query(IndustriaFuente).order_by(IndustriaFuente.id_industria).all()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar industrias.") from exc


@router.get("/{id_industria}", response_model=IndustriaResponse)
def obtener_industria(id_industria: int, db: Session = Depends(get_db)):
    try:
        industria = (
            db.query(IndustriaFuente)
            .filter(IndustriaFuente.id_industria == id_industria)
            .first()
        )
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=500, detail="Error al consultar la industria.") from exc

    if industria is None:
        raise HTTPException(status_code=404, detail="Industria no encontrada.")
    return industria
