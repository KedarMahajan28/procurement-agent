"""
LangGraph orchestration for the full pipeline:

  ingest -> extract -> normalize/store -> analyze (comparison+bundling+risk)
  -> decide -> [END, awaits human approval via the API]

This mirrors the workflow diagram in the spec (section 22). Low-confidence
extractions are routed to human review rather than silently stored.
"""
import os
from typing import TypedDict

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from .extraction_agent import extract_quote_from_text, normalize_and_store
from .decision_agent import generate_recommendations

CONFIDENCE_THRESHOLD = 0.6


class PipelineState(TypedDict):
    document_paths: list[str]
    extraction_results: list[dict]
    needs_review: list[dict]
    recommendations_count: int


def build_graph(db: Session):
    def ingest_and_extract(state: PipelineState) -> PipelineState:
        results = []
        needs_review = []
        for path in state["document_paths"]:
            with open(path, "r") as f:
                text = f.read()
            filename = os.path.basename(path)
            extracted = extract_quote_from_text(text, filename)
            stored = normalize_and_store(db, extracted, confidence_threshold=CONFIDENCE_THRESHOLD)
            results.append(stored)
            if stored["needs_human_review"]:
                needs_review.append(stored)
        state["extraction_results"] = results
        state["needs_review"] = needs_review
        return state

    def analyze_and_decide(state: PipelineState) -> PipelineState:
        recs = generate_recommendations(db, persist=True)
        state["recommendations_count"] = len(recs)
        return state

    graph = StateGraph(PipelineState)
    graph.add_node("ingest_and_extract", ingest_and_extract)
    graph.add_node("analyze_and_decide", analyze_and_decide)
    graph.set_entry_point("ingest_and_extract")
    graph.add_edge("ingest_and_extract", "analyze_and_decide")
    graph.add_edge("analyze_and_decide", END)
    return graph.compile()


def run_pipeline(db: Session, document_paths: list[str]) -> PipelineState:
    app = build_graph(db)
    initial: PipelineState = {
        "document_paths": document_paths,
        "extraction_results": [],
        "needs_review": [],
        "recommendations_count": 0,
    }
    return app.invoke(initial)
