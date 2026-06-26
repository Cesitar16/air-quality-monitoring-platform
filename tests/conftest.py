import os
import sys
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_DIR = Path(__file__).resolve().parents[1]
API_DIR = ROOT_DIR / "api"

if str(API_DIR) not in sys.path:
    sys.path.insert(0, str(API_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite:///./tests_bootstrap.sqlite3")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Comuna, EstacionSensor, IndustriaFuente, MonitoreoAmbiental  # noqa: E402


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test_api.sqlite3"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    session = testing_session_local()
    session.add_all(
        [
            Comuna(
                id_comuna=1,
                nombre="Talca",
                region="Maule",
                poblacion_estimada=250000,
                indice_vulnerabilidad_respiratoria=64.2,
            ),
            Comuna(
                id_comuna=2,
                nombre="Chillan",
                region="Nuble",
                poblacion_estimada=198000,
                indice_vulnerabilidad_respiratoria=72.8,
            ),
        ]
    )
    session.add_all(
        [
            EstacionSensor(
                id_estacion=1,
                codigo_unico="SEN-TAL-OF-001",
                tipo="publico_oficial",
                latitud=-35.4264,
                longitud=-71.6554,
                id_comuna=1,
            ),
            EstacionSensor(
                id_estacion=2,
                codigo_unico="SEN-CHI-ONG-001",
                tipo="sensor_comunitario_ong",
                latitud=-36.6152,
                longitud=-72.1185,
                id_comuna=2,
            ),
        ]
    )
    session.add_all(
        [
            IndustriaFuente(
                id_industria=1,
                nombre="Industria Talca",
                rubro_industrial="Celulosa",
                emision_maxima_permitida=420.0,
                id_comuna=1,
            ),
            IndustriaFuente(
                id_industria=3,
                nombre="Industria Talca 2",
                rubro_industrial="Agroindustria",
                emision_maxima_permitida=210.0,
                id_comuna=1,
            ),
            IndustriaFuente(
                id_industria=2,
                nombre="Industria Chillan",
                rubro_industrial="Calderas industriales",
                emision_maxima_permitida=180.0,
                id_comuna=2,
            ),
        ]
    )
    session.add_all(
        [
            MonitoreoAmbiental(
                id_monitoreo=1,
                fecha_hora=datetime(2026, 6, 18, 0, 0, 0),
                id_estacion=1,
                mp25=65.0,
                mp10=110.0,
                so2=12.0,
                no2=18.0,
                velocidad_viento=2.5,
                direccion_viento_grados=180.0,
                temperatura=9.0,
                humedad=70.0,
            ),
            MonitoreoAmbiental(
                id_monitoreo=2,
                fecha_hora=datetime(2026, 6, 18, 6, 0, 0),
                id_estacion=2,
                mp25=115.0,
                mp10=160.0,
                so2=20.0,
                no2=28.0,
                velocidad_viento=1.5,
                direccion_viento_grados=90.0,
                temperatura=6.0,
                humedad=85.0,
            ),
        ]
    )
    session.commit()
    session.close()

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
