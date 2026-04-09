"""Confluence API client package."""

from app.integrations.clients.confluence.client import (
    ConfluenceClient,
    ConfluenceValidationResult,
    build_confluence_config,
    confluence_config_from_env,
    make_confluence_client,
    search_relevant_documents,
    validate_confluence_config,
)
from app.integrations.models import ConfluenceIntegrationConfig

__all__ = [
    "ConfluenceClient",
    "ConfluenceIntegrationConfig",
    "ConfluenceValidationResult",
    "build_confluence_config",
    "confluence_config_from_env",
    "make_confluence_client",
    "search_relevant_documents",
    "validate_confluence_config",
]
