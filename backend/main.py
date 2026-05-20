"""
main.py

The FastAPI server for the research agent pipeline.
This file exposes the LangGraph research pipeline as a REST API.

Endpoints:
    POST /research      → runs the full agent pipeline
                          returns the final report and sources
    GET  /health        → health check endpoint
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph import research_graph

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
    print(f"\n🚀 Starting research pipeline for: {request.query}")

    try:
        # Invoke the LangGraph pipeline with initial state
        result = research_graph.invoke({
            "query": request.query,
            "sources": [],
            "summary": "",
            "fact_check": "",
            "report": "",
            "status": "starting"
        })

        print(f"\n✅ Pipeline complete")

        return ResearchResponse(
            query=request.query,
            report=result["report"],
            sources=result["sources"],
            status=result["status"]
        )

    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Research pipeline failed: {str(e)}"
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