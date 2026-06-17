from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import SessionLocal
from app.routes.comunas import router as comunas_router
from app.routes.estaciones import router as estaciones_router
from app.routes.industrias import router as industrias_router
from app.routes.monitoreo import router as monitoreo_router
from app.schemas import HealthResponse

app = FastAPI(
    title="Monitoreo de Calidad del Aire API",
    description="API REST para consultar comunas, estaciones, industrias y monitoreo ambiental.",
    version="1.0.0",
)


@app.get("/", tags=["Health"])
def root():
    return {"message": "API Monitoreo de Calidad del Aire disponible."}


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(status="ok", database="connected")
    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "database": "disconnected"},
        )
    finally:
        db.close()


app.include_router(comunas_router)
app.include_router(estaciones_router)
app.include_router(industrias_router)
app.include_router(monitoreo_router)
