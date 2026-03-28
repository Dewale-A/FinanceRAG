"""Tests for FinanceRAG API endpoints."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_200(self):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self):
        """Health response should contain status field."""
        response = client.get("/health")
        data = response.json()
        assert "status" in data

    def test_health_returns_settings(self):
        """Health response should contain settings."""
        response = client.get("/health")
        data = response.json()
        assert "settings" in data
        assert "llm_model" in data["settings"]


class TestRootEndpoint:
    """Test the root endpoint."""

    def test_root_returns_200(self):
        """Root endpoint should return 200."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_api_info(self):
        """Root should return API name and version."""
        response = client.get("/")
        data = response.json()
        assert data["name"] == "FinanceRAG API"
        assert data["version"] == "1.0.0"


class TestStatsEndpoint:
    """Test the stats endpoint."""

    def test_stats_returns_200(self):
        """Stats endpoint should return 200."""
        response = client.get("/stats")
        assert response.status_code == 200


class TestQueryEndpoint:
    """Test the query endpoint validation."""

    def test_query_requires_question(self):
        """Query should reject empty requests."""
        response = client.post("/query", json={})
        assert response.status_code == 422

    def test_query_rejects_short_question(self):
        """Query should reject questions shorter than 3 chars."""
        response = client.post("/query", json={"question": "ab"})
        assert response.status_code == 422

    def test_query_rejects_invalid_k(self):
        """Query should reject k values outside valid range."""
        response = client.post("/query", json={"question": "test question", "k": 0})
        assert response.status_code == 422


class TestIngestEndpoint:
    """Test the ingest endpoint validation."""

    def test_ingest_requires_source_path(self):
        """Ingest should reject empty requests."""
        response = client.post("/ingest", json={})
        assert response.status_code == 422

    def test_ingest_rejects_invalid_path(self):
        """Ingest should return 404 for non-existent paths."""
        response = client.post("/ingest", json={"source_path": "/nonexistent/path"})
        assert response.status_code == 404
