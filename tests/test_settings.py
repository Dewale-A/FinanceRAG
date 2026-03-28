"""Tests for FinanceRAG settings."""

import pytest
from src.config.settings import Settings, get_settings


class TestSettings:
    """Test application settings."""

    def test_settings_loads(self):
        """Settings should load without error."""
        settings = get_settings()
        assert settings is not None

    def test_default_llm_model(self):
        """Default LLM model should be gpt-4o-mini."""
        settings = get_settings()
        assert settings.llm_model == "gpt-4o-mini"

    def test_default_embedding_model(self):
        """Default embedding model should be text-embedding-ada-002."""
        settings = get_settings()
        assert settings.embedding_model == "text-embedding-ada-002"

    def test_default_chunk_size(self):
        """Default chunk size should be 1000."""
        settings = get_settings()
        assert settings.chunk_size == 1000

    def test_default_chunk_overlap(self):
        """Default chunk overlap should be 200."""
        settings = get_settings()
        assert settings.chunk_overlap == 200

    def test_default_top_k(self):
        """Default top_k should be 5."""
        settings = get_settings()
        assert settings.top_k_results == 5

    def test_default_api_port(self):
        """Default API port should be 8000."""
        settings = get_settings()
        assert settings.api_port == 8000
