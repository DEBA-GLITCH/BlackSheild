
# Conditional edge routing functions for the BlackSheild graph.
#
# LangGraph conditional edges:
#   - You register a function that receives the current state.
#   - The function returns a string (single route) or list of strings (fan-out).
#   - LangGraph maps that to a node name via the path_map in builder.py.
#
# Rules for edge functions:
#   - Pure with respect to side effects: read state, return a route string only.
#   - Deterministic: same state always produces same route.
#   - Never raise exceptions: if routing logic fails, return a safe default.
#   - Returned strings must exactly match path_map keys in builder.py.

from blacksheild.core.state import BlackSheildState


def route_after_intake(state: BlackSheildState) -> list[str] | str:
    """
    Routes after the intake node completes.

    Path 1 - Cache hit:
        intake found a valid cached result for this target.
        Return a single string "report" to skip all fetch/normalize/score work.

    Path 2 - Fresh run:
        No cache entry or it has expired.
        Return a list of three node names - LangGraph launches all three
        concurrently as a fan-out. Results merge via operator.add reducers.

    Args:
        state: current BlackSheildState after intake_node has run.

    Returns:
        "report" (string) for cache hit, or
        ["fetch_nvd", "fetch_github", "fetch_osv"] (list) for fresh run.
    """
    if state.get("cache_hit", False):
        # Single string -> LangGraph routes to exactly one node.
        # The report node reads the cached report from state and writes it out.
        return "report"

    # List of strings -> LangGraph launches all three concurrently.
    # Their outputs merge into state via operator.add on raw_*_findings.
    return ["fetch_nvd", "fetch_github", "fetch_osv"]


def route_after_fetch(state: BlackSheildState) -> str:
    """
    Extension point: routing after all fetch nodes complete (fan-in point).

    Currently unused - we use direct edges from each fetch node to normalize.
    Kept here as a documented hook for future dead-letter routing.

    Future use case: if all three fetches fail and produce zero raw data,
    you could route directly to report instead of running normalize on nothing.
    For now, normalize handles empty input gracefully and we always continue.

    Args:
        state: current BlackSheildState after all fetch nodes have run.

    Returns:
        Node name to route to next.
    """
    all_raw_empty = (
        not state.get("raw_nvd_findings")
        and not state.get("raw_github_findings")
        and not state.get("raw_osv_findings")
    )

    # Even with all-empty raw data, route to normalize.
    # It produces an empty normalized_findings list.
    # The report surfaces the errors from state["errors"].
    if all_raw_empty:
        return "normalize"

    return "normalize"