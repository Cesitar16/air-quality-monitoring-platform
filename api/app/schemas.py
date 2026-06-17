from datetime import date, datetime

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
    codigo_sensor: str
    nombre: str
    tipo: str
    latitud: float
    longitud: float
    id_comuna: int
    activo: bool


class EstacionResponse(EstacionBase):
    model_config = ConfigDict(from_attributes=True)

    id_estacion: int
    fecha_instalacion: date | None = None


class IndustriaBase(BaseModel):
    nombre: str
    rubro_industrial: str
    latitud: float
    longitud: float
    id_comuna: int
    emision_maxima_permitida: float
    unidad_emision: str | None = None
    activa: bool


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
    temperatura: float = Field(ge=-20, le=50)
    humedad: float = Field(ge=0, le=100)
    fuente_dato: str = Field(default="api_fastapi", min_length=1, max_length=50)


class MonitoreoTableResponse(MonitoreoCreate):
    model_config = ConfigDict(from_attributes=True)

    id_monitoreo: int
    nivel_riesgo: str | None = None


class MonitoreoDetalleResponse(BaseModel):
    id_monitoreo: int
    fecha_hora: datetime
    comuna: str
    region: str
    poblacion_estimada: int
    indice_vulnerabilidad_respiratoria: float
    codigo_sensor: str
    estacion: str
    tipo_sensor: str
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
    nivel_riesgo: str | None = None
    fuente_dato: str


class ResumenComunaResponse(BaseModel):
    comuna: str
    region: str
    total_mediciones: int
    promedio_mp25: float
    maximo_mp25: float
    promedio_mp10: float
    promedio_temperatura: float
    promedio_humedad: float
    promedio_viento: float
    dias_o_periodos_criticos: int


class DatasetMLResponse(BaseModel):
    id_monitoreo: int
    hora: float
    dia_semana: float
    comuna: str
    region: str
    codigo_sensor: str
    mp25: float
    mp10: float
    so2: float
    no2: float
    velocidad_viento: float
    direccion_viento_grados: float
    temperatura: float
    humedad: float
    indice_vulnerabilidad_respiratoria: float
    nivel_riesgo: str | None = None
