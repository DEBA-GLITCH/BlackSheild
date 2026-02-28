
# Embed node - upserts findings into the Chroma vector store.
#
# Responsibilities (full implementation in Phase 5):
#   1. Read normalized_findings from state.
#   2. Generate embeddings for each finding (description + metadata).
#   3. Upsert into Chroma collection (idempotent - same ID = update not duplicate).
#   4. On Chroma failure, append to state["errors"] and continue.
#      A report without embeddings is still a valid output.
#
# Node contract:
#   Reads:   normalized_findings, correlation_id
#   Writes:  completed_nodes, errors

from blacksheild.core.state import BlackSheildState


def embed_node(state: BlackSheildState) -> dict:
    """Stub. Full implementation in Phase 5."""
    return {
        "completed_nodes": ["embed"],
    }