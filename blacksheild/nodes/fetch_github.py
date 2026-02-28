# Fetch node for the GitHub Advisory Database (GHSA) via GraphQL API.
#
# Responsibilities (full implementation in Phase 3):
#   1. Query GitHub's GraphQL security advisory API.
#   2. Filter by package name and ecosystem.
#   3. Return raw GHSA response dicts into state["raw_github_findings"].
#   4. On failure, catch, log, append to state["errors"], return empty list.
#
# Node contract:
#   Reads:   target, correlation_id
#   Writes:  raw_github_findings, completed_nodes, errors

from blacksheild.core.state import BlackSheildState


def fetch_github_node(state: BlackSheildState) -> dict:
    """Stub. Full implementation in Phase 3."""
    return {
        "raw_github_findings": [],
        "completed_nodes": ["fetch_github"],
    }