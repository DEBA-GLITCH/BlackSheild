
# Constructs and compiles the BlackSheild LangGraph StateGraph.
#
# This file owns the graph topology:
#   - Which nodes exist
#   - How they connect
#   - Which edges are conditional
#
# Node implementations live in blacksheild/nodes/.
# Conditional edge logic lives in blacksheild/graph/edges.py.
#
# The compiled graph returned by build_graph() is the object you call
# .invoke() or .ainvoke() on. Once compiled, the graph is immutable.
#
# LangSmith traces at the compiled graph boundary - every .ainvoke() call
# becomes one trace in LangSmith with child spans for each node.

from langgraph.graph import END, START, StateGraph

from blacksheild.core.state import BlackSheildState
from blacksheild.graph.edges import route_after_intake
from blacksheild.nodes.intake import intake_node
from blacksheild.nodes.fetch_nvd import fetch_nvd_node
from blacksheild.nodes.fetch_github import fetch_github_node
from blacksheild.nodes.fetch_osv import fetch_osv_node
from blacksheild.nodes.normalize import normalize_node
from blacksheild.nodes.correlate import correlate_node
from blacksheild.nodes.score import score_node
from blacksheild.nodes.embed import embed_node
from blacksheild.nodes.report import report_node


# Node name constants - define once, use everywhere.
# String literals scattered across builder and edges are a maintenance hazard.
NODE_INTAKE        = "intake"
NODE_FETCH_NVD     = "fetch_nvd"
NODE_FETCH_GITHUB  = "fetch_github"
NODE_FETCH_OSV     = "fetch_osv"
NODE_NORMALIZE     = "normalize"
NODE_CORRELATE     = "correlate"
NODE_SCORE         = "score"
NODE_EMBED         = "embed"
NODE_REPORT        = "report"


def build_graph():
    """
    Constructs and returns the compiled BlackSheild LangGraph runnable.

    Graph topology:

                          START
                            |
                        [ intake ]
                       /          \\
              (cache hit)      (fresh run)
                  |                 |
              [ report ]    fan-out (parallel):
                  |          [ fetch_nvd ]
                 END         [ fetch_github ]
                             [ fetch_osv ]
                                  |
                             fan-in to:
                            [ normalize ]
                                  |
                            [ correlate ]
                                  |
                              [ score ]
                                  |
                              [ embed ]
                                  |
                             [ report ]
                                  |
                                 END

    Fan-out:
        LangGraph runs fetch_nvd, fetch_github, fetch_osv concurrently
        because route_after_intake returns a list of three node names.
        Results merge via operator.add reducers on raw_*_findings fields.

    Fan-in (sync barrier):
        normalize only starts after all three fetch nodes complete.
        LangGraph handles this automatically - all three edges point to normalize.

    Returns:
        Compiled LangGraph runnable. Call .invoke(state) or .ainvoke(state).
    """
    graph = StateGraph(BlackSheildState)

    # ------------------------------------------------------------------
    # Register all nodes
    # ------------------------------------------------------------------
    graph.add_node(NODE_INTAKE,       intake_node)
    graph.add_node(NODE_FETCH_NVD,    fetch_nvd_node)
    graph.add_node(NODE_FETCH_GITHUB, fetch_github_node)
    graph.add_node(NODE_FETCH_OSV,    fetch_osv_node)
    graph.add_node(NODE_NORMALIZE,    normalize_node)
    graph.add_node(NODE_CORRELATE,    correlate_node)
    graph.add_node(NODE_SCORE,        score_node)
    graph.add_node(NODE_EMBED,        embed_node)
    graph.add_node(NODE_REPORT,       report_node)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    graph.add_edge(START, NODE_INTAKE)

    # ------------------------------------------------------------------
    # Conditional routing after intake:
    #   cache hit  -> skip all work, go straight to report
    #   fresh run  -> fan out to all three fetch nodes in parallel
    # ------------------------------------------------------------------
    graph.add_conditional_edges(
        NODE_INTAKE,
        route_after_intake,
        {
            NODE_FETCH_NVD:    NODE_FETCH_NVD,
            NODE_FETCH_GITHUB: NODE_FETCH_GITHUB,
            NODE_FETCH_OSV:    NODE_FETCH_OSV,
            NODE_REPORT:       NODE_REPORT,
        },
    )

    # ------------------------------------------------------------------
    # Fan-in: all three fetch nodes converge on normalize.
    # LangGraph waits for all three before executing normalize.
    # A failed fetch node still routes here - normalize handles empty input.
    # ------------------------------------------------------------------
    graph.add_edge(NODE_FETCH_NVD,    NODE_NORMALIZE)
    graph.add_edge(NODE_FETCH_GITHUB, NODE_NORMALIZE)
    graph.add_edge(NODE_FETCH_OSV,    NODE_NORMALIZE)

    # ------------------------------------------------------------------
    # Linear pipeline after normalization
    # ------------------------------------------------------------------
    graph.add_edge(NODE_NORMALIZE, NODE_CORRELATE)
    graph.add_edge(NODE_CORRELATE, NODE_SCORE)
    graph.add_edge(NODE_SCORE,     NODE_EMBED)
    graph.add_edge(NODE_EMBED,     NODE_REPORT)

    # ------------------------------------------------------------------
    # Terminal
    # ------------------------------------------------------------------
    graph.add_edge(NODE_REPORT, END)

    return graph.compile()