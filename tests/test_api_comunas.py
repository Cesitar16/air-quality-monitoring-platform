def test_get_comunas_devuelve_lista(client):
    response = client.get("/comunas")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


def test_get_comuna_inexistente_devuelve_404(client):
    response = client.get("/comunas/999")

    assert response.status_code == 404
    assert "id_comuna=999" in response.json()["detail"]
