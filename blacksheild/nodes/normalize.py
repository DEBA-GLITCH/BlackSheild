
# Normalize node - maps raw API responses to the unified Finding schema.
#
# Responsibilities (full implementation in Phase 3):
#   1. Read raw_nvd_findings, raw_github_findings, raw_osv_findings from state.
#   2. Map each raw dict to the unified Finding Pydantic model (schema/finding.py).
#   3. Log and skip individual findings that fail validation (do not abort run).
#   4. Write normalized_findings as list of dicts (model.dict()).
#
# Node contract:
#   Reads:   raw_nvd_findings, raw_github_findings, raw_osv_findings
#   Writes:  normalized_findings, completed_nodes, errors

from blacksheild.core.state import BlackSheildState


def normalize_node(state: BlackSheildState) -> dict:
    """Stub. Full implementation in Phase 3."""
    return {
        "normalized_findings": [],
        "completed_nodes": ["normalize"],
    }