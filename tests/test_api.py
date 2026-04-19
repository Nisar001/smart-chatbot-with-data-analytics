from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routes.health_routes import router as health_router


def test_health_route_returns_ok():
    app = FastAPI()
    app.include_router(health_router, prefix="/api/v1")
    client = TestClient(app)

    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"
