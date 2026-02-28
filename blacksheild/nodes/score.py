
# Score node - computes risk scores per finding and in aggregate.
#
# Responsibilities (full implementation in Phase 4):
#   1. Read normalized_findings and correlation_groups from state.
#   2. Compute per-finding risk score using CVSS base score + contextual modifiers.
#   3. Compute aggregate_risk_score for the whole analysis run.
#   4. Write risk_scores (list) and aggregate_risk_score (float) to state.
#
# Node contract:
#   Reads:   normalized_findings, correlation_groups
#   Writes:  risk_scores, aggregate_risk_score, completed_nodes, errors

from blacksheild.core.state import BlackSheildState


def score_node(state: BlackSheildState) -> dict:
    """Stub. Full implementation in Phase 4."""
    return {
        "risk_scores": [],
        "aggregate_risk_score": None,
        "completed_nodes": ["score"],
    }