from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import get_db
from app.routes.analytics import router as analytics_router
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
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return HealthResponse(
            status="ok",
            service="air-quality-api",
            database="connected",
        )
    except SQLAlchemyError:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "service": "air-quality-api",
                "database": "disconnected",
            },
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Error de validacion en la solicitud.",
            "errores": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno controlado en la API."},
    )


app.include_router(comunas_router)
app.include_router(estaciones_router)
app.include_router(industrias_router)
app.include_router(monitoreo_router)
app.include_router(analytics_router)
