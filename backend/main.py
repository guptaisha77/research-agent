"""
main.py

The FastAPI server for the research agent pipeline.
This file exposes the LangGraph research pipeline as a REST API.

Endpoints:
    POST /research          → runs the full agent pipeline
                              returns the final report and sources
    GET /research/stream   → runs the full agent pipeline
                              streams live agent updates via SSE
    GET /health            → health check endpoint
"""

import json
import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from pipeline import run_pipeline, stream_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ──────────────────────────────────────────────────────────
app = FastAPI(
    title="Research Agent API",
    description="""
A multi-agent AI research pipeline built with LangGraph and FastAPI.

## How it works

1. **Search Agent** — searches the web for relevant sources
2. **Summariser Agent** — condenses the sources into a summary
3. **Fact Checker Agent** — cross-references the summary against sources
4. **Writer Agent** — composes a structured final report

## Try it out

Use the `/research` endpoint below to run the full pipeline.

Example queries:
- `Build me a knowledge base on Python async programming`
- `Build me a knowledge base on machine learning fundamentals`
- `What is retrieval augmented generation?`
    """,
    version="1.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────
# Placeholder — allows all origins during development
# Update allow_origins to the frontend URL (when we build it)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request / Response Models ────────────────────────────────────
# Pydantic models to define the shape of request and response
class ResearchRequest(BaseModel):
    """The request body for the research endpoint."""
    query: str

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Build me a knowledge base on Python async programming"
            }
        }


class ResearchResponse(BaseModel):
    """The response body from the research endpoint."""
    query: str
    report: str
    sources: list
    status: str


# ── SSE Helper ───────────────────────────────────────────────────

def format_sse(data: dict) -> str:
    """
    Formats a dictionary as an SSE event string.

    SSE events must follow this exact format:
        data: <json string>\n\n
    The double newline at the end signals the end of one event.
    The frontend's EventSource reads each event as it arrives.

    Example output:
        data: {"agent": "search", "status": "running"}\n\n
    """
    return f"data: {json.dumps(data)}\n\n"


# ── Endpoints ────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """
    Health check endpoint.
    Returns 200 if the server is running.
    """
    return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
def run_research(request: ResearchRequest):
    """
    Runs the full multi-agent research pipeline.

    Takes a query and runs it through four agents in sequence:
    search → summariser → fact_checker → writer

    Returns the final structured report and sources.
    """
    logger.info("Starting research pipeline for: %s", request.query)

    try:
        result = run_pipeline(request.query)

        logger.info("Pipeline complete for: %s", request.query)

        return ResearchResponse(
            query=request.query,
            report=result["report"],
            sources=result["sources"],
            status=result["status"]
        )

    except Exception as e:
        logger.exception("Pipeline error for query: %s", request.query)
        raise HTTPException(
            status_code=500,
            detail="Research pipeline failed. Check server logs for details."
        )


@app.get("/research/stream")
def stream_research(query: str):
    """
    Streams live agent updates as the pipeline runs.

    Takes a query as a URL parameter and streams SSE events
    as each agent starts and finishes.

    Each event is a JSON object with:
    - agent: which agent is running
    - status: 'running' or 'done'
    - message: a human-readable status message
    - data: the agent's output (only on 'done' events)

    Example usage:
        GET /research/stream?query=Build me a knowledge base on Python

    Connect via EventSource in the browser:
        const source = new EventSource('/research/stream?query=...')
        source.onmessage = (e) => console.log(JSON.parse(e.data))
    """

    logger.info("Starting streaming pipeline for: %s", query)

    def event_generator():
        for event in stream_pipeline(query):
            yield format_sse(event)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Run ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )