def test_health_responde_200(client):
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "air-quality-api"
    assert data["database"] == "connected"
