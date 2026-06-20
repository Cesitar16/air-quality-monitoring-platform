def test_get_monitoreo_devuelve_lista(client):
    response = client.get("/monitoreo")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_post_monitoreo_valido_funciona(client):
    payload = {
        "fecha_hora": "2026-06-19T00:00:00",
        "id_estacion": 1,
        "mp25": 44.5,
        "mp10": 80.0,
        "so2": 10.0,
        "no2": 12.0,
        "velocidad_viento": 3.1,
        "direccion_viento_grados": 135.0,
        "temperatura": 11.0,
        "humedad": 60.0,
    }
    response = client.post("/monitoreo", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id_estacion"] == 1
    assert data["mp25"] == 44.5


def test_post_monitoreo_invalido_falla(client):
    payload = {
        "fecha_hora": "2026-06-19T00:00:00",
        "id_estacion": 1,
        "mp25": -1,
        "mp10": 80.0,
        "so2": 10.0,
        "no2": 12.0,
        "velocidad_viento": 3.1,
        "direccion_viento_grados": 135.0,
        "temperatura": 11.0,
        "humedad": 60.0,
    }
    response = client.post("/monitoreo", json=payload)

    assert response.status_code == 422


def test_post_monitoreo_bulk_funciona(client):
    payload = {
        "mediciones": [
            {
                "fecha_hora": "2026-06-19T06:00:00",
                "id_estacion": 1,
                "mp25": 48.0,
                "mp10": 82.0,
                "so2": 11.0,
                "no2": 13.0,
                "velocidad_viento": 2.8,
                "direccion_viento_grados": 150.0,
                "temperatura": 10.0,
                "humedad": 58.0,
            },
            {
                "fecha_hora": "2026-06-19T12:00:00",
                "id_estacion": 2,
                "mp25": 89.0,
                "mp10": 120.0,
                "so2": 15.0,
                "no2": 22.0,
                "velocidad_viento": 1.2,
                "direccion_viento_grados": 200.0,
                "temperatura": 13.0,
                "humedad": 52.0,
            },
        ]
    }
    response = client.post("/monitoreo/bulk", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["insertados"] == 2
    assert data["errores"] == 0


def test_post_monitoreo_bulk_controla_duplicados_por_estacion_y_fecha(client):
    payload = {
        "mediciones": [
            {
                "fecha_hora": "2026-06-20T00:00:00",
                "id_estacion": 1,
                "mp25": 49.0,
                "mp10": 85.0,
                "so2": 11.0,
                "no2": 14.0,
                "velocidad_viento": 2.1,
                "direccion_viento_grados": 170.0,
                "temperatura": 9.5,
                "humedad": 59.0,
            },
            {
                "fecha_hora": "2026-06-20T00:00:00",
                "id_estacion": 1,
                "mp25": 50.0,
                "mp10": 86.0,
                "so2": 11.5,
                "no2": 14.5,
                "velocidad_viento": 2.0,
                "direccion_viento_grados": 171.0,
                "temperatura": 9.0,
                "humedad": 60.0,
            },
        ]
    }
    response = client.post("/monitoreo/bulk", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["insertados"] == 1
    assert data["errores"] == 1
    assert "Ya existe una medicion para esa estacion y fecha_hora" in data["detalle_errores"][0]["motivo"]


def test_get_monitoreo_limita_valor_maximo_de_limit(client):
    response = client.get("/monitoreo?limit=999999")

    assert response.status_code == 422
