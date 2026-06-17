from sqlalchemy import BigInteger, Boolean, Column, Date, DateTime, ForeignKey, Integer
from sqlalchemy import Numeric, String, Text
from sqlalchemy.sql import func

from app.database import Base


class Comuna(Base):
    __tablename__ = "comunas"

    id_comuna = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    region = Column(String(50), nullable=False)
    poblacion_estimada = Column(Integer, nullable=False)
    indice_vulnerabilidad_respiratoria = Column(Numeric(5, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class EstacionSensor(Base):
    __tablename__ = "estaciones_sensores"

    id_estacion = Column(Integer, primary_key=True, index=True)
    codigo_sensor = Column(String(50), nullable=False, unique=True)
    nombre = Column(String(120), nullable=False)
    tipo = Column(String(50), nullable=False)
    latitud = Column(Numeric(9, 6), nullable=False)
    longitud = Column(Numeric(9, 6), nullable=False)
    id_comuna = Column(Integer, ForeignKey("comunas.id_comuna"), nullable=False)
    activo = Column(Boolean, default=True)
    fecha_instalacion = Column(Date)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class IndustriaFuente(Base):
    __tablename__ = "industrias_fuentes"

    id_industria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    rubro_industrial = Column(String(100), nullable=False)
    latitud = Column(Numeric(9, 6), nullable=False)
    longitud = Column(Numeric(9, 6), nullable=False)
    id_comuna = Column(Integer, ForeignKey("comunas.id_comuna"), nullable=False)
    emision_maxima_permitida = Column(Numeric(10, 2), nullable=False)
    unidad_emision = Column(String(30))
    activa = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp())


class MonitoreoAmbiental(Base):
    __tablename__ = "monitoreo_ambiental"

    id_monitoreo = Column(BigInteger, primary_key=True, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    id_estacion = Column(Integer, ForeignKey("estaciones_sensores.id_estacion"), nullable=False)
    mp25 = Column(Numeric(8, 2), nullable=False)
    mp10 = Column(Numeric(8, 2), nullable=False)
    so2 = Column(Numeric(8, 2), nullable=False)
    no2 = Column(Numeric(8, 2), nullable=False)
    velocidad_viento = Column(Numeric(6, 2), nullable=False)
    direccion_viento_grados = Column(Numeric(6, 2), nullable=False)
    temperatura = Column(Numeric(5, 2), nullable=False)
    humedad = Column(Numeric(5, 2), nullable=False)
    fuente_dato = Column(String(50), nullable=False)
    nivel_riesgo = Column(String(20))
    created_at = Column(DateTime, server_default=func.current_timestamp())
