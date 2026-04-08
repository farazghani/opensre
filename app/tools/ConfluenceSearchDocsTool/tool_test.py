from __future__ import annotations

from unittest.mock import patch

import pytest

from app.integrations.clients.confluence import ConfluenceConfig
from app.tools.ConfluenceSearchDocsTool import (
    _resolve_config,
    search_confluence_docs,
)


@pytest.fixture()
def env_config() -> ConfluenceConfig:
    return ConfluenceConfig.model_validate(
        {
            "base_url": "https://example.atlassian.net",
            "email": "sre@example.com",
            "api_token": "token_123",
            "space_key": "SRE",
        }
    )


def test_resolve_config_prefers_explicit_args_over_env(env_config: ConfluenceConfig) -> None:
    with patch(
        "app.tools.ConfluenceSearchDocsTool.confluence_config_from_env",
        return_value=env_config,
    ):
        config = _resolve_config(
            confluence_base_url="https://override.atlassian.net",
            confluence_email="override@example.com",
            confluence_api_token="override-token",
            space_key="OPS",
        )

    assert config is not None
    assert config.base_url == "https://override.atlassian.net"
    assert config.email == "override@example.com"
    assert config.api_token == "override-token"
    assert config.space_key == "OPS"


def test_resolve_config_uses_env_when_args_missing(env_config: ConfluenceConfig) -> None:
    with patch(
        "app.tools.ConfluenceSearchDocsTool.confluence_config_from_env",
        return_value=env_config,
    ):
        config = _resolve_config(
            confluence_base_url=None,
            confluence_email=None,
            confluence_api_token=None,
            space_key=None,
        )

    assert config is not None
    assert config.base_url == env_config.base_url
    assert config.email == env_config.email
    assert config.api_token == env_config.api_token
    assert config.space_key == env_config.space_key


def test_search_confluence_docs_returns_unavailable_without_credentials() -> None:
    with patch(
        "app.tools.ConfluenceSearchDocsTool.confluence_config_from_env",
        return_value=None,
    ):
        result = search_confluence_docs(query="database outage")

    assert result["available"] is False
    assert result["source"] == "confluence"
    assert result["results"] == []
    assert "not configured" in result["error"].lower()


def test_search_confluence_docs_passes_through_search_result_shape(env_config: ConfluenceConfig) -> None:
    confluence_result = {
        "success": True,
        "results": [
            {
                "id": "123",
                "title": "Runbook: Database Outage",
                "excerpt": "Steps for restoring the cluster",
                "url": "https://example.atlassian.net/wiki/spaces/SRE/pages/123",
                "entity_type": "page",
                "score": 0.98,
                "space_key": "SRE",
                "space_name": "Site Reliability Engineering",
                "last_modified": "2026-04-08T00:00:00Z",
                "labels": ["runbook"],
            }
        ],
        "total": 1,
        "size": 1,
        "limit": 10,
        "query": "database outage",
        "cql": 'type = page AND (label in ("runbook"))',
        "space_key": "SRE",
        "cursor": None,
        "next_cursor": "",
        "prev_cursor": "",
    }

    with patch(
        "app.tools.ConfluenceSearchDocsTool.confluence_config_from_env",
        return_value=env_config,
    ), patch(
        "app.tools.ConfluenceSearchDocsTool.search_relevant_documents",
        return_value=confluence_result,
    ) as mock_search:
        result = search_confluence_docs(query="database outage", limit=10)

    mock_search.assert_called_once()
    assert result["available"] is True
    assert result["source"] == "confluence"
    assert result["results"] == confluence_result["results"]
    assert result["total"] == 1
    assert result["size"] == 1
    assert result["query"] == "database outage"
    assert result["cql"] == confluence_result["cql"]
    assert result["space_key"] == "SRE"
