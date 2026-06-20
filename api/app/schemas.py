from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: str
    service: str
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


class MonitoreoBulkCreate(BaseModel):
    mediciones: list[dict[str, Any]]


class MonitoreoBulkError(BaseModel):
    indice: int
    motivo: str


class MonitoreoBulkResponse(BaseModel):
    insertados: int
    errores: int
    detalle_errores: list[MonitoreoBulkError]


class MonitoreoDetalleResponse(BaseModel):
    id_monitoreo: int
    fecha_hora: datetime
    id_estacion: int
    id_comuna: int
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


class AnalyticsResumen(BaseModel):
    total_comunas: int
    total_estaciones: int
    total_industrias: int
    total_mediciones: int
    mp25_promedio: float
    mp25_maximo: float
    comuna_mas_critica: str | None = None


class AnalyticsMp25PorComuna(BaseModel):
    comuna: str
    region: str
    mp25_promedio: float
    cantidad_mediciones: int


class AnalyticsComunaCritica(BaseModel):
    comuna: str
    region: str
    mp25_promedio: float
    mp25_maximo: float
    categoria: str


class AnalyticsEvolucionMp25(BaseModel):
    fecha: date
    comuna: str
    mp25_promedio: float


class AnalyticsIcaPorComuna(BaseModel):
    comuna: str
    region: str
    mp25_promedio: float
    categoria: str
    mensaje_ciudadano: str
    color_referencial: str


class AnalyticsRankingSensor(BaseModel):
    id_estacion: int
    codigo_estacion: str
    tipo_sensor: str
    comuna: str
    mp25_promedio: float
    cantidad_mediciones: int


class DatasetModelado(BaseModel):
    fecha_hora: datetime
    comuna: str
    region: str
    codigo_estacion: str
    tipo_sensor: str
    mp25: float
    mp10: float
    so2: float
    no2: float
    velocidad_viento: float
    direccion_viento_grados: float
    temperatura: float
    humedad: float
    indice_vulnerabilidad_respiratoria: float
    emision_maxima_permitida: float | None = None
    categoria_ica: str
