
# LangGraph state schema for BlackSheild.
# This is the single source of truth for everything flowing through the graph.
#
# Architecture rules enforced here:
#   1. Every field has an explicit type annotation.
#   2. Fields written by multiple nodes (fan-out) use Annotated[list, operator.add]
#      so LangGraph concatenates instead of replacing.
#   3. Fields written by exactly one node use plain types (default replace).
#   4. No business logic here - this is a pure data contract.
#
# How LangGraph uses this:
#   - define a TypedDict subclass.
#   - pass it to StateGraph(YourState).
#   - Every node receives the full current state and returns a partial dict
#     containing only the keys it updates.
#   - LangGraph merges the partial dict using reducers:
#       Default reducer            -> replaces the value
#       Annotated[list, add]       -> appends to the list

import operator
from typing import Annotated, Any, TypedDict


# ------------------------------------------------------------------
# Sub-types used within state fields.
# Plain TypedDicts here - Pydantic models in schema/ handle final validation.
# Using plain dicts in state keeps LangGraph serialization simple.
# ------------------------------------------------------------------

class TargetInput(TypedDict):
    """
    The user-supplied analysis target, parsed and validated by the intake node.

    type:      "domain" | "package" | "org"
    value:     the normalized target string, e.g. "requests" or "example.com"
    ecosystem: only relevant for packages, e.g. "PyPI", "npm", "Go"
    """
    type: str
    value: str
    ecosystem: str | None


class ErrorEntry(TypedDict):
    """
    A structured error record appended to state['errors'] by any node
    that encounters a recoverable failure.

    node:       which node produced this error
    error_type: the exception class name
    message:    human-readable description
    context:    arbitrary key-value pairs for debugging
    """
    node: str
    error_type: str
    message: str
    context: dict[str, Any]


# ------------------------------------------------------------------
# Main state schema
# ------------------------------------------------------------------

class BlackSheildState(TypedDict):
    """
    The complete state that flows through the BlackSheild LangGraph.

    Sections:
      CONTROL   - orchestration metadata, not business data
      RAW DATA  - unprocessed API responses, one entry per finding per source
      PROCESSED - normalized, correlated, and scored findings
      OUTPUT    - final report artifact
      ERRORS    - accumulated failures from all nodes
    """

    # ------------------------------------------------------------------
    # CONTROL
    # ------------------------------------------------------------------

    # Unique ID for this analysis run. Set by initial_state(), read everywhere.
    # Format: "bs-{uuid4}"  e.g. "bs-4f3a1c2d-..."
    # Used as the correlation ID in all structured log entries.
    correlation_id: str

    # The validated and parsed target from the user.
    target: TargetInput

    # Tracks which nodes completed successfully this run.
    # Uses operator.add so each node appends its own name without overwriting others.
    # Example after full run: ["intake", "fetch_nvd", "fetch_github", "fetch_osv", ...]
    completed_nodes: Annotated[list[str], operator.add]

    # True if the intake node found a valid cached result for this target today.
    # When True, the graph routes directly to report, skipping all fetch/normalize/score.
    cache_hit: bool

    # ------------------------------------------------------------------
    # RAW DATA
    # ------------------------------------------------------------------
    # Each field holds the raw API response dicts from that source.
    # Annotated with operator.add because a paginating client could write
    # multiple chunks. Also required for correctness in fan-out.

    raw_nvd_findings: Annotated[list[dict[str, Any]], operator.add]
    raw_github_findings: Annotated[list[dict[str, Any]], operator.add]
    raw_osv_findings: Annotated[list[dict[str, Any]], operator.add]

    # ------------------------------------------------------------------
    # PROCESSED
    # ------------------------------------------------------------------

    # All findings after normalization into the unified Finding schema (as dicts).
    # operator.add supports extending normalize to run in sub-graphs per source.
    normalized_findings: Annotated[list[dict[str, Any]], operator.add]

    # Correlation groups from the correlate node.
    # Each entry: {"canonical_id": str, "related_ids": list[str], ...}
    # Written by exactly one node - plain list, default replace reducer.
    correlation_groups: list[dict[str, Any]]

    # Risk scores from the score node.
    # Each entry: {"finding_id": str, "score": float, "severity": str}
    risk_scores: list[dict[str, Any]]

    # Aggregate risk score for this entire analysis run. 0.0 to 10.0.
    aggregate_risk_score: float | None

    # ------------------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------------------

    # The final structured report as a serializable dict.
    # Populated by the report node as the last step.
    report: dict[str, Any] | None

    # Absolute path to the JSON report file written to disk.
    report_path: str | None

    # ------------------------------------------------------------------
    # ERROR TRACKING
    # ------------------------------------------------------------------

    # Accumulated errors from all nodes. Each node appends its own failures.
    # operator.add ensures parallel fetch nodes do not overwrite each other.
    # The report node reads this and includes a failure summary section.
    errors: Annotated[list[ErrorEntry], operator.add]


def initial_state(correlation_id: str, target: TargetInput) -> BlackSheildState:
    """
    Returns a fully-initialized state dict with all fields set to safe empty defaults.

    This is the state you pass to graph.invoke() as the starting point.
    Every field must be present - LangGraph will KeyError on first node access
    if any field is missing from the initial state.

    Args:
        correlation_id: pre-generated run ID, format "bs-{uuid4}"
        target:         validated TargetInput from the caller

    Returns:
        A BlackSheildState ready for graph invocation.
    """
    return BlackSheildState(
        # Control
        correlation_id=correlation_id,
        target=target,
        completed_nodes=[],
        cache_hit=False,
        # Raw data - empty, populated by fetch nodes
        raw_nvd_findings=[],
        raw_github_findings=[],
        raw_osv_findings=[],
        # Processed - empty until normalize/correlate/score nodes run
        normalized_findings=[],
        correlation_groups=[],
        risk_scores=[],
        aggregate_risk_score=None,
        # Output - None until report node runs
        report=None,
        report_path=None,
        # Errors - empty, nodes append on failure
        errors=[],
    )