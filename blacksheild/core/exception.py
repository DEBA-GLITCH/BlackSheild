
# Domain-specific exception hierarchy for BlackSheild.
#
# Design rules:
#   - Every exception carries enough context to produce a structured log entry.
#   - No bare `raise Exception(...)` anywhere in the codebase. Always use these.
#   - Nodes catch these and write to state["errors"]. They never propagate to LangGraph.
#   - Only truly unrecoverable situations (invalid config at startup) let an
#     exception escape a node boundary.

from __future__ import annotations


class BlackSheildError(Exception):
    """
    Base class for all BlackSheild exceptions.

    Carries a human-readable message and an optional dict of structured context
    that will be included in the log entry and the error state field.
    """

    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.context: dict = context or {}

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for appending to state['errors']."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
        }


# ------------------------------------------------------------------
# Configuration errors
# ------------------------------------------------------------------

class ConfigurationError(BlackSheildError):
    """
    Raised at startup when required configuration is missing or invalid.
    This one IS allowed to propagate - there is no point starting a run
    with broken config.
    """


# ------------------------------------------------------------------
# API client errors
# ------------------------------------------------------------------

class APIClientError(BlackSheildError):
    """Base class for all external API failures."""

    def __init__(
        self,
        message: str,
        source: str,
        status_code: int | None = None,
        context: dict | None = None,
    ) -> None:
        ctx = context or {}
        ctx["source"] = source
        if status_code is not None:
            ctx["status_code"] = status_code
        super().__init__(message, ctx)
        self.source = source
        self.status_code = status_code


class APIRateLimitError(APIClientError):
    """
    HTTP 429 or equivalent rate limit response.
    Tenacity will catch this and apply backoff before retry.
    """


class APIAuthError(APIClientError):
    """
    HTTP 401 or 403. Likely a missing or expired API key.
    Retrying will not help - surface immediately, do not retry.
    """


class APITimeoutError(APIClientError):
    """
    The external API did not respond within the configured timeout.
    Tenacity will retry with backoff.
    """


class APIResponseParseError(APIClientError):
    """
    The API returned 2xx but the response body could not be parsed
    into the expected schema. Indicates a breaking API change upstream.
    """


# ------------------------------------------------------------------
# Graph / node errors
# ------------------------------------------------------------------

class NodeExecutionError(BlackSheildError):
    """
    Wraps an unexpected error inside a node execution.
    The node catches this, logs it, and writes it to state['errors'].
    """

    def __init__(self, message: str, node_name: str, context: dict | None = None) -> None:
        ctx = context or {}
        ctx["node_name"] = node_name
        super().__init__(message, ctx)
        self.node_name = node_name


class InvalidTargetError(BlackSheildError):
    """
    The user-supplied target (domain, package, org) failed validation.
    Raised in the intake node before any API calls are made.
    """


# ------------------------------------------------------------------
# Normalization / schema errors
# ------------------------------------------------------------------

class NormalizationError(BlackSheildError):
    """
    A raw API finding could not be mapped to the unified Finding schema.
    Individual failures are logged and skipped - they do not abort the run.
    """

    def __init__(
        self,
        message: str,
        source: str,
        raw_data: dict,
        context: dict | None = None,
    ) -> None:
        ctx = context or {}
        ctx["source"] = source
        # Store only keys to avoid bloating logs with huge raw payloads
        ctx["raw_data_keys"] = list(raw_data.keys()) if raw_data else []
        super().__init__(message, ctx)
        self.source = source
        self.raw_data = raw_data


# ------------------------------------------------------------------
# Vector store errors
# ------------------------------------------------------------------

class VectorStoreError(BlackSheildError):
    """
    Chroma operation failed (upsert, query, etc.).
    The embed node catches this and writes to state['errors'],
    but the run continues - a report without embeddings is still valid output.
    """


# ------------------------------------------------------------------
# Idempotency errors
# ------------------------------------------------------------------

class IdempotencyError(BlackSheildError):
    """
    The idempotency cache itself failed (read or write error).
    Non-fatal: on cache read failure we proceed as a fresh run.
    On cache write failure we log and continue - report is still produced.
    """