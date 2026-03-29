"""Tests for FinanceRAG API authentication."""

import os
import pytest
from fastapi.testclient import TestClient


class TestAuthWhenDisabled:
    """Test that endpoints work when API_KEY is not set."""

    def test_query_accessible_without_key(self):
        """Query should work without API key when auth is disabled."""
        # Auth is disabled when API_KEY env var is not set
        os.environ.pop("API_KEY", None)
        from src.api.main import app
        client = TestClient(app)
        response = client.post("/query", json={"question": "test question here"})
        # Should not get 403 (might get 500 if no docs, but not 403)
        assert response.status_code != 403

    def test_health_always_public(self):
        """Health endpoint should always be accessible."""
        from src.api.main import app
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200

    def test_root_always_public(self):
        """Root endpoint should always be accessible."""
        from src.api.main import app
        client = TestClient(app)
        response = client.get("/")
        assert response.status_code == 200

    def test_stats_always_public(self):
        """Stats endpoint should always be accessible."""
        from src.api.main import app
        client = TestClient(app)
        response = client.get("/stats")
        assert response.status_code == 200
