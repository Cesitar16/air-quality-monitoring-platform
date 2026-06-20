from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint

from app.database import Base


class Comuna(Base):
    __tablename__ = "comunas"

    id_comuna = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    region = Column(String(50), nullable=False)
    poblacion_estimada = Column(Integer, nullable=False)
    indice_vulnerabilidad_respiratoria = Column(Numeric(5, 2), nullable=False)


class EstacionSensor(Base):
    __tablename__ = "estaciones_sensores"

    id_estacion = Column(Integer, primary_key=True, index=True)
    codigo_unico = Column(String(50), nullable=False, unique=True)
    tipo = Column(String(50), nullable=False)
    latitud = Column(Numeric(9, 6), nullable=False)
    longitud = Column(Numeric(9, 6), nullable=False)
    id_comuna = Column(Integer, ForeignKey("comunas.id_comuna"), nullable=False)


class IndustriaFuente(Base):
    __tablename__ = "industrias_fuentes"

    id_industria = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False)
    rubro_industrial = Column(String(100), nullable=False)
    emision_maxima_permitida = Column(Numeric(10, 2), nullable=False)
    id_comuna = Column(Integer, ForeignKey("comunas.id_comuna"), nullable=False)


class MonitoreoAmbiental(Base):
    __tablename__ = "monitoreo_ambiental"
    __table_args__ = (
        UniqueConstraint(
            "id_estacion",
            "fecha_hora",
            name="uk_monitoreo_ambiental_estacion_fecha",
        ),
    )

    id_monitoreo = Column(Integer, primary_key=True, index=True)
    fecha_hora = Column(DateTime, nullable=False)
    id_estacion = Column(Integer, ForeignKey("estaciones_sensores.id_estacion"), nullable=False)
    mp25 = Column(Numeric(8, 2), nullable=False)
    mp10 = Column(Numeric(8, 2), nullable=False)
    so2 = Column(Numeric(8, 2), nullable=False)
    no2 = Column(Numeric(8, 2), nullable=False)
    velocidad_viento = Column(Numeric(6, 2), nullable=False)
    direccion_viento_grados = Column(Numeric(5, 2), nullable=False)
    temperatura = Column(Numeric(5, 2), nullable=False)
    humedad = Column(Numeric(5, 2), nullable=False)
