from langgraph.graph import END, START, StateGraph

from app.core.config import Settings
from app.graph.nodes import (
    analyze_query_node,
    construct_context_node,
    document_safety_node,
    make_generation_node,
    make_retrieval_node,
    no_evidence_node,
    route_after_input_validation,
    route_after_document_safety,
    route_after_output_validation,
    route_after_retrieval,
    safe_response_node,
    validate_input_node,
    validate_output_node,
)
from app.graph.state import RAGState


def build_rag_graph(settings: Settings):
    builder = StateGraph(RAGState)
    builder.add_node("input_validation", validate_input_node)
    builder.add_node("query_analysis", analyze_query_node)
    builder.add_node("retrieval", make_retrieval_node(settings))
    builder.add_node("document_safety", document_safety_node)
    builder.add_node("context_construction", construct_context_node)
    builder.add_node("generation", make_generation_node(settings))
    builder.add_node("output_validation", validate_output_node)
    builder.add_node("no_evidence", no_evidence_node)
    builder.add_node("safe_response", safe_response_node)

    builder.add_edge(START, "input_validation")
    builder.add_conditional_edges(
        "input_validation",
        route_after_input_validation,
        {"query_analysis": "query_analysis", "safe_response": "safe_response"},
    )
    builder.add_edge("query_analysis", "retrieval")
    builder.add_conditional_edges(
        "retrieval",
        route_after_retrieval,
        {"document_safety": "document_safety", "no_evidence": "no_evidence"},
    )
    builder.add_conditional_edges(
        "document_safety",
        route_after_document_safety,
        {"context_construction": "context_construction", "no_evidence": "no_evidence"},
    )
    builder.add_edge("context_construction", "generation")
    builder.add_edge("generation", "output_validation")
    builder.add_conditional_edges(
        "output_validation",
        route_after_output_validation,
        {"end": END, "safe_response": "safe_response"},
    )
    builder.add_edge("no_evidence", END)
    builder.add_edge("safe_response", END)
    return builder.compile()
