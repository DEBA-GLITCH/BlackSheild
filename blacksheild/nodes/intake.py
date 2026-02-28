
# Intake node - the graph entry point.
#
# Responsibilities (full implementation in Phase 3):
#   1. Validate the target input (domain/package/org name).
#   2. Generate a correlation_id for this run.
#   3. Check the idempotency cache. If a valid result exists today,
#      load it into state and set cache_hit=True.
#   4. Log the run start with correlation_id and target.
#
# Node contract:
#   Reads:   target (must be pre-populated via initial_state())
#   Writes:  correlation_id, cache_hit, completed_nodes, errors

from blacksheild.core.state import BlackSheildState


def intake_node(state: BlackSheildState) -> dict:
    """
    Intake node stub. Full implementation in Phase 3.
    """
    return {
        "completed_nodes": ["intake"],
        "cache_hit": False,
    }