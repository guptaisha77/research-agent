"""
pipeline.py

Service layer for the research pipeline and SSE stage streaming.
"""

from typing import Any, Dict, Generator, List

from graph import run_search, run_summariser, run_fact_checker, run_writer

PipelineState = Dict[str, Any]
PipelineEvent = Dict[str, Any]


def initial_state(query: str) -> PipelineState:
    return {
        "query": query,
        "sources": [],
        "summary": "",
        "fact_check": "",
        "report": "",
        "status": "starting"
    }


def run_pipeline(query: str) -> PipelineState:
    state = initial_state(query)

    state.update(run_search(state))
    state.update(run_summariser(state))
    state.update(run_fact_checker(state))
    state.update(run_writer(state))

    state["status"] = "complete"
    return state


def format_stage_event(agent: str, status: str, message: str, data: Any = None) -> PipelineEvent:
    event: PipelineEvent = {
        "agent": agent,
        "status": status,
        "message": message,
    }
    if data is not None:
        event["data"] = data
    return event


def stream_pipeline(query: str) -> Generator[PipelineEvent, None, None]:
    state = initial_state(query)

    stages: List[tuple[str, str, Any]] = [
        ("search", "Searching sources...", run_search),
        ("summariser", "Summarising sources...", run_summariser),
        ("fact_checker", "Checking facts...", run_fact_checker),
        ("writer", "Writing final report...", run_writer),
    ]

    for agent, message, stage_fn in stages:
        yield format_stage_event(agent, "running", f"{message}")
        updates = stage_fn(state)
        state.update(updates)

        data = None
        if agent == "search":
            data = {"sources": state["sources"]}
        elif agent == "summariser":
            data = {"summary": state["summary"]}
        elif agent == "fact_checker":
            data = {"fact_check": state["fact_check"]}
        elif agent == "writer":
            data = {"report": state["report"]}

        yield format_stage_event(
            agent,
            "done",
            f"{agent.replace('_', ' ').title()} complete",
            data,
        )

    state["status"] = "complete"
    yield format_stage_event(
        "pipeline",
        "complete",
        "Pipeline complete",
        {
            "report": state["report"],
            "sources": state["sources"],
            "status": state["status"],
        },
    )
