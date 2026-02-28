
# Fetch node for the OSV (Open Source Vulnerabilities) API.
# No API key required. https://osv.dev/docs/
#
# Responsibilities (full implementation in Phase 3):
#   1. POST to the OSV batch query endpoint with package name + ecosystem.
#   2. Return raw OSV response dicts into state["raw_osv_findings"].
#   3. On failure, catch, log, append to state["errors"], return empty list.
#
# Node contract:
#   Reads:   target, correlation_id
#   Writes:  raw_osv_findings, completed_nodes, errors

from blacksheild.core.state import BlackSheildState


def fetch_osv_node(state: BlackSheildState) -> dict:
    """Stub. Full implementation in Phase 3."""
    return {
        "raw_osv_findings": [],
        "completed_nodes": ["fetch_osv"],
    }