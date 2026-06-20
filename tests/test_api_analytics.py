def test_resumen_general_responde_estructura_esperada(client):
    response = client.get("/analytics/resumen-general")

    assert response.status_code == 200
    data = response.json()
    assert "total_comunas" in data
    assert "mp25_promedio" in data
    assert "comuna_mas_critica" in data


def test_mp25_por_comuna_responde_estructura_esperada(client):
    response = client.get("/analytics/mp25-por-comuna")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert "comuna" in data[0]
    assert "mp25_promedio" in data[0]


def test_ica_por_comuna_responde_categoria(client):
    response = client.get("/analytics/ica-por-comuna")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["categoria"] in {
        "Buena",
        "Regular",
        "Alerta",
        "Preemergencia",
        "Emergencia",
    }


def test_dataset_modelado_no_duplica_filas_por_multiples_industrias(client):
    response = client.get("/analytics/dataset-modelado?limit=10")

    assert response.status_code == 200
    data = response.json()
    fechas_estacion = {
        (fila["fecha_hora"], fila["codigo_estacion"])
        for fila in data
    }
    assert len(data) == len(fechas_estacion)
