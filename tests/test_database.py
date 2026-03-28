"""Tests for FinanceRAG database module."""

import pytest
from src.database import Base, QueryLog, DocumentMetadata


class TestModels:
    """Test database model definitions."""

    def test_query_log_table_name(self):
        """QueryLog should use correct table name."""
        assert QueryLog.__tablename__ == "query_logs"

    def test_document_metadata_table_name(self):
        """DocumentMetadata should use correct table name."""
        assert DocumentMetadata.__tablename__ == "document_metadata"

    def test_query_log_has_required_columns(self):
        """QueryLog should have all required columns."""
        columns = [c.name for c in QueryLog.__table__.columns]
        assert "id" in columns
        assert "question" in columns
        assert "answer" in columns
        assert "model" in columns
        assert "documents_retrieved" in columns
        assert "timestamp" in columns
        assert "response_time_ms" in columns

    def test_document_metadata_has_required_columns(self):
        """DocumentMetadata should have all required columns."""
        columns = [c.name for c in DocumentMetadata.__table__.columns]
        assert "id" in columns
        assert "filename" in columns
        assert "file_type" in columns
        assert "chunk_count" in columns
        assert "ingested_at" in columns
        assert "status" in columns
