"""Tests for configuration and lane presets."""

from __future__ import annotations

import os

import pytest

from code_rag_py_mcp.config import LANE_PRESETS, McpSettings


def test_lane_presets_keys() -> None:
    assert set(LANE_PRESETS) == {"balanced", "func", "call", "class"}


def test_mcp_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
    monkeypatch.setenv("MCP_TRANSPORT", "http")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "4444")
    settings = McpSettings.from_env()
    assert settings.transport == "http"
    assert settings.host == "0.0.0.0"
    assert settings.port == 4444
    assert settings.path == "/mcp"


def test_database_url_required(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        McpSettings.from_env()
