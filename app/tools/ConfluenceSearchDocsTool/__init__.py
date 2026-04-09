"""Confluence runbook and operational document search tool."""

from __future__ import annotations

from typing import Any

from app.integrations.clients.confluence import (
    build_confluence_config,
    confluence_config_from_env,
    search_relevant_documents,
)
from app.integrations.models import ConfluenceIntegrationConfig
from app.tools.tool_decorator import tool


def _resolve_config(
    confluence_base_url: str | None,
    confluence_email: str | None,
    confluence_api_token: str | None,
    space_key: str | None = None,
) -> ConfluenceIntegrationConfig | None:
    env_config = confluence_config_from_env()
    if any([confluence_base_url, confluence_email, confluence_api_token]) or (
        space_key and env_config is not None
    ):
        config = build_confluence_config(
            {
                "base_url": confluence_base_url or (env_config.base_url if env_config else ""),
                "email": confluence_email or (env_config.email if env_config else ""),
                "api_token": confluence_api_token or (env_config.api_token if env_config else ""),
                "space_key": space_key or (env_config.space_key if env_config else ""),
            }
        )
        if not (config.base_url and config.email and config.api_token):
            return None
        return config
    return env_config


def _confluence_available(sources: dict[str, dict]) -> bool:
    return bool(sources.get("confluence", {}).get("connection_verified"))


def _confluence_creds(confluence: dict[str, Any]) -> dict[str, Any]:
    return {
        "confluence_base_url": confluence.get("base_url"),
        "confluence_email": confluence.get("email"),
        "confluence_api_token": confluence.get("api_token"),
        "space_key": confluence.get("space_key", ""),
    }


def _search_confluence_docs_extract_params(sources: dict[str, dict]) -> dict[str, Any]:
    confluence = sources["confluence"]
    return {
        "query": confluence.get("query") or "runbook OR incident OR operational",
        "limit": 10,
        "include_archived_spaces": False,
        **_confluence_creds(confluence),
    }


@tool(
    name="search_confluence_docs",
    source="confluence",
    description="Search Confluence for incident runbooks, docs, and operational pages.",
    use_cases=[
        "Finding a runbook during an active incident",
        "Searching for operational documentation related to a crash",
        "Looking up internal docs that describe a service's recovery process",
    ],
    requires=["query"],
    surfaces=("investigation", "chat"),
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 10},
            "include_archived_spaces": {"type": "boolean", "default": False},
            "space_key": {"type": "string", "default": ""},
            "confluence_base_url": {"type": "string"},
            "confluence_email": {"type": "string"},
            "confluence_api_token": {"type": "string"},
        },
        "required": ["query"],
    },
    outputs={
        "results": "Matching Confluence pages with titles, excerpts, URLs, and metadata",
        "total": "Total number of results returned",
        "query": "Effective search query used for the CQL search",
        "cql": "Generated Confluence Query Language filter",
    },
    is_available=_confluence_available,
    extract_params=_search_confluence_docs_extract_params,
)
def search_confluence_docs(
    query: str,
    confluence_base_url: str | None = None,
    confluence_email: str | None = None,
    confluence_api_token: str | None = None,
    space_key: str = "",
    limit: int = 10,
    include_archived_spaces: bool = False,
    **_kwargs: Any,
) -> dict[str, Any]:
    """Search Confluence for runbooks, docs, and operational pages relevant to an incident."""
    config = _resolve_config(confluence_base_url, confluence_email, confluence_api_token, space_key or None)
    if config is None:
        return {
            "source": "confluence",
            "available": False,
            "error": "Confluence integration is not configured.",
            "results": [],
        }

    # Confluence API caps search results at 25.
    limit = min(max(limit, 1), 25)
    result = search_relevant_documents(
        config,
        query=query,
        limit=limit,
        space_key=space_key or None,
        include_archived_spaces=include_archived_spaces,
    )
    if not result.get("success"):
        return {
            "source": "confluence",
            "available": False,
            "error": result.get("error", "Unknown error"),
            "results": [],
            "query": query,
        }

    return {
        "source": "confluence",
        "available": True,
        "results": result.get("results", []),
        "total": result.get("total", 0),
        "size": result.get("size", 0),
        "limit": result.get("limit", limit),
        "query": result.get("query", query),
        "cql": result.get("cql", ""),
        "space_key": result.get("space_key", space_key or ""),
        "cursor": result.get("cursor"),
        "next_cursor": result.get("next_cursor", ""),
        "prev_cursor": result.get("prev_cursor", ""),
    }
