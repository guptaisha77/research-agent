"""
graph.py

The LangGraph orchestrator for the research agent pipeline.
This file defines the state, nodes, and edges that connect
all agents into a single agentic flow.

The flow is:
    intent → [if guide] → search → summariser → fact_checker → writer → github_agent
                       [if research] → search → summariser → fact_checker → writer

State is passed between agents and updated at each step.
Each agent adds its results to the shared state.
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END
from agents.intent import intent_agent
from agents.search import search_agent
from agents.summariser import summariser_agent
from agents.fact_checker import fact_checker_agent
from agents.writer import writer_agent
from agents.github_agent import github_agent


# ── State ────────────────────────────────────────────────────────
class ResearchState(TypedDict):
    query: str          # the original question from the user
    intent: str         # 'guide' or 'research' - filled by intent agent
    sources: list       # filled by search agent
    summary: str        # filled by summariser agent
    fact_check: str     # filled by fact checker agent
    report: str         # filled by writer agent
    repo_url: str       # filled by github agent (only for guide intent)
    status: str         # tracks which agent is currently running


# ── Nodes ────────────────────────────────────────────────────────
def run_intent(state: ResearchState) -> dict:
    """Runs the Intent Agent and determines the workflow path."""
    print("\n--- Running Intent Agent ---")
    result = intent_agent(state["query"])
    return {
        "intent": result["intent"],
        "status": "intent_done"
    }


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
        state["sources"],
        state.get("intent", "research")
    )
    return {
        "report": result["report"],
        "status": "writer_done"
    }


def run_github(state: ResearchState) -> dict:
    """Runs the GitHub Agent and creates a repository (guide intent only)."""
    print("\n--- Running GitHub Agent ---")
    result = github_agent(
        state["query"],
        state["report"],
        state["summary"],
        state["fact_check"],
        state["sources"]
    )
    return {
        "repo_url": result.get("repo_url", ""),
        "status": "github_done"
    }


# ── Conditional Routing ─────────────────────────────────────────
def route_after_writer(state: ResearchState) -> Literal["github_agent", "end"]:
    """
    Routes to GitHub Agent if intent is 'guide', otherwise ends.
    """
    if state.get("intent") == "guide":
        return "github_agent"
    else:
        return "end"


# ── Graph ────────────────────────────────────────────────────────
def build_graph():
    """
    Builds and compiles the LangGraph research pipeline with conditional routing.
    Returns a compiled graph ready to run.
    
    Flow:
        intent → search → summariser → fact_checker → writer → [if guide] → github_agent
                                                                [if research] → END
    """
    graph = StateGraph(ResearchState)

    # Add all nodes
    graph.add_node("intent_agent", run_intent)
    graph.add_node("search", run_search)
    graph.add_node("summariser", run_summariser)
    graph.add_node("fact_checker", run_fact_checker)
    graph.add_node("writer", run_writer)
    graph.add_node("github_agent", run_github)

    # Set entry point
    graph.set_entry_point("intent_agent")

    # Linear edges: intent → search → summariser → fact_checker → writer
    graph.add_edge("intent_agent", "search")
    graph.add_edge("search", "summariser")
    graph.add_edge("summariser", "fact_checker")
    graph.add_edge("fact_checker", "writer")

    # Conditional routing after writer
    graph.add_conditional_edges(
        "writer",
        route_after_writer,
        {
            "github_agent": "github_agent",
            "end": END
        }
    )

    # GitHub agent routes to end
    graph.add_edge("github_agent", END)

    return graph.compile()


# Single compiled instance imported by main.py
research_graph = build_graph()