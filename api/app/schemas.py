from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    database: str


class ComunaBase(BaseModel):
    nombre: str
    region: str
    poblacion_estimada: int
    indice_vulnerabilidad_respiratoria: float


class ComunaResponse(ComunaBase):
    model_config = ConfigDict(from_attributes=True)

    id_comuna: int


class EstacionBase(BaseModel):
    codigo_unico: str
    tipo: str
    latitud: float
    longitud: float
    id_comuna: int


class EstacionResponse(EstacionBase):
    model_config = ConfigDict(from_attributes=True)

    id_estacion: int


class IndustriaBase(BaseModel):
    nombre: str
    rubro_industrial: str
    id_comuna: int
    emision_maxima_permitida: float


class IndustriaResponse(IndustriaBase):
    model_config = ConfigDict(from_attributes=True)

    id_industria: int


class MonitoreoCreate(BaseModel):
    fecha_hora: datetime
    id_estacion: int
    mp25: float = Field(ge=0)
    mp10: float = Field(ge=0)
    so2: float = Field(ge=0)
    no2: float = Field(ge=0)
    velocidad_viento: float = Field(ge=0)
    direccion_viento_grados: float = Field(ge=0, le=360)
    temperatura: float = Field(ge=-50, le=60)
    humedad: float = Field(ge=0, le=100)


class MonitoreoDetalleResponse(BaseModel):
    id_monitoreo: int
    fecha_hora: datetime
    comuna: str
    region: str
    poblacion_estimada: int
    indice_vulnerabilidad_respiratoria: float
    codigo_unico: str
    tipo: str
    latitud: float
    longitud: float
    mp25: float
    mp10: float
    so2: float
    no2: float
    velocidad_viento: float
    direccion_viento_grados: float
    temperatura: float
    humedad: float
