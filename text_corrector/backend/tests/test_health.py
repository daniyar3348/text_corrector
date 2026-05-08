"""
Unit tests for the /health endpoint.
"""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_returns_200(self):
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_schema(self):
        response = client.get("/health")
        data = response.json()
        assert "service_status" in data
        assert "model_status" in data
        assert "version" in data

    def test_service_status_ok(self):
        response = client.get("/health")
        data = response.json()
        assert data["service_status"] == "ok"

    def test_model_status_value(self):
        response = client.get("/health")
        data = response.json()
        # Either "loaded" (real model) or "placeholder" (mock)
        assert data["model_status"] in ("loaded", "placeholder")

    def test_version_present(self):
        response = client.get("/health")
        data = response.json()
        assert isinstance(data["version"], str)
        assert len(data["version"]) > 0
