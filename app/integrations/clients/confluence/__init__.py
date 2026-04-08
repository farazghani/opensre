"""Confluence API client package."""

from app.integrations.clients.confluence.client import (
    ConfluenceClient,
    ConfluenceConfig,
    ConfluenceValidationResult,
    build_confluence_config,
    confluence_config_from_env,
    make_confluence_client,
    search_relevant_documents,
    validate_confluence_config,
)

__all__ = [
    "ConfluenceClient",
    "ConfluenceConfig",
    "ConfluenceValidationResult",
    "build_confluence_config",
    "confluence_config_from_env",
    "make_confluence_client",
    "search_relevant_documents",
    "validate_confluence_config",
]
