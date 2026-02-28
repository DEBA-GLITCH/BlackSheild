
# Correlate node - deduplicates findings and groups related CVEs.
#
# Responsibilities (full implementation in Phase 4):
#   1. Read normalized_findings from state.
#   2. Deduplicate by CVE ID across sources (same CVE from NVD and OSV = one finding).
#   3. Build correlation groups: related CVEs, chains, affected version ranges.
#   4. Write correlation_groups to state.
#
# Node contract:
#   Reads:   normalized_findings
#   Writes:  correlation_groups, completed_nodes, errors

from blacksheild.core.state import BlackSheildState


def correlate_node(state: BlackSheildState) -> dict:
    """Stub. Full implementation in Phase 4."""
    return {
        "correlation_groups": [],
        "completed_nodes": ["correlate"],
    }