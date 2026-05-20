"""
graph.py

The LangGraph orchestrator for the research agent pipeline.
This file defines the state, nodes, and edges that connect
all four agents into a single agentic flow.

The flow is:
    search → summariser → fact_checker → writer

State is passed between agents and updated at each step.
Each agent adds its results to the shared state.
"""

from typing import TypedDict
from langgraph.graph import StateGraph, END
from agents.search import search_agent
from agents.summariser import summariser_agent
from agents.fact_checker import fact_checker_agent
from agents.writer import writer_agent


# ── State ────────────────────────────────────────────────────────
class ResearchState(TypedDict):
    query: str          # the original question from the user
    sources: list       # filled by search agent
    summary: str        # filled by summariser agent
    fact_check: str     # filled by fact checker agent
    report: str         # filled by writer agent
    status: str         # tracks which agent is currently running


# ── Nodes ────────────────────────────────────────────────────────
def run_search(state: ResearchState) -> dict:
    """Runs the Search Agent and adds sources to state."""
    print("\n--- Running Search Agent ---")
    result = search_agent(state["query"])
    return {
        "sources": result["sources"],
        "status": "search_done"
    }


def run_summariser(state: ResearchState) -> dict:
    """Runs the Summariser Agent and adds summary to state."""
    print("\n--- Running Summariser Agent ---")
    result = summariser_agent(state["sources"])
    return {
        "summary": result["summary"],
        "status": "summariser_done"
    }


def run_fact_checker(state: ResearchState) -> dict:
    """Runs the Fact Checker Agent and adds findings to state."""
    print("\n--- Running Fact Checker Agent ---")
    result = fact_checker_agent(state["summary"], state["sources"])
    return {
        "fact_check": result["flags"],
        "status": "fact_checker_done"
    }


def run_writer(state: ResearchState) -> dict:
    """Runs the Writer Agent and adds final report to state."""
    print("\n--- Running Writer Agent ---")
    result = writer_agent(
        state["query"],
        state["summary"],
        state["fact_check"],
        state["sources"]
    )
    return {
        "report": result["report"],
        "status": "writer_done"
    }


# ── Graph ────────────────────────────────────────────────────────
def build_graph():
    """
    Builds and compiles the LangGraph research pipeline.
    Returns a compiled graph ready to run.
    """
    graph = StateGraph(ResearchState)

    graph.add_node("search", run_search)
    graph.add_node("summariser", run_summariser)
    graph.add_node("fact_checker", run_fact_checker)
    graph.add_node("writer", run_writer)

    graph.set_entry_point("search")

    graph.add_edge("search", "summariser")
    graph.add_edge("summariser", "fact_checker")
    graph.add_edge("fact_checker", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


# Single compiled instance imported by main.py
research_graph = build_graph()