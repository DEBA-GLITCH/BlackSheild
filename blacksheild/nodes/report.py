
# Report node - serializes the final structured JSON report.
#
# Responsibilities (full implementation in Phase 6):
#   1. Read normalized_findings, correlation_groups, risk_scores,
#      aggregate_risk_score, errors, and target from state.
#   2. Build the final ThreatReport Pydantic model (schema/report.py).
#   3. Serialize to JSON and write to reports/{correlation_id}.json.
#   4. Write report (dict) and report_path (str) to state.
#
# Node contract:
#   Reads:   normalized_findings, correlation_groups, risk_scores,
#            aggregate_risk_score, errors, target, correlation_id
#   Writes:  report, report_path, completed_nodes

from blacksheild.core.state import BlackSheildState


def report_node(state: BlackSheildState) -> dict:
    """Stub. Full implementation in Phase 6."""
    return {
        "report": {"status": "stub", "correlation_id": state.get("correlation_id")},
        "report_path": None,
        "completed_nodes": ["report"],
    }