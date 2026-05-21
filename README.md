# Research Agent

A modular AI research pipeline that transforms a natural language query into a structured research report.

This project demonstrates how to build a chained multi-agent workflow for research tasks, with each agent responsible for one clear step in the process. The backend exposes a clean REST API and is implemented using FastAPI, LangGraph, Groq, and Tavily.

## Project overview

The research pipeline is designed to solve a common problem: how to gather, condense, verify, and present information from the web in a reliable way.

The current implementation performs these steps:

- Search the web for relevant sources
- Summarise the collected information
- Fact check the summary against the sources
- Write a polished final report with citations

## Pipeline diagram

```text
User query
     |
     v
Search Agent
     |
     v
Summariser Agent
     |
     v
Fact Checker Agent
     |
     v
Writer Agent
     |
     v
Final report + sources
```

## How the pipeline works

### 1. Search Agent
- Located in `backend/agents/search.py`
- Uses the Tavily search client to gather relevant web sources
- Returns a cleaned list of source objects containing title, URL, and content

### 2. Summariser Agent
- Located in `backend/agents/summariser.py`
- Reads the collected sources and generates a concise summary
- Limits output length using the configured summary word count

### 3. Fact Checker Agent
- Located in `backend/agents/fact_checker.py`
- Compares the summary against the original sources
- Identifies unsupported claims or confirms that the facts are verified

### 4. Writer Agent
- Located in `backend/agents/writer.py`
- Combines the query, summary, fact-check notes, and source list
- Produces a final report with introduction, key findings, conclusion, and citations

## Architecture

The orchestration logic lives in `backend/graph.py` and the runtime service lives in `backend/pipeline.py`.

### `backend/graph.py` — graph definition
- Declares the LangGraph pipeline as a state graph.
- Defines the nodes and transitions between:
  - `search`
  - `summariser`
  - `fact_checker`
  - `writer`
- Acts as the **blueprint** for the research flow.

### `backend/pipeline.py` — execution and streaming
- Runs the same agents in sequence.
- Produces the actual research state and results.
- Powers both the standard API and the SSE streaming endpoint.
- Converts the graph blueprint into runtime behavior.

### How they relate

```text
backend/graph.py          backend/pipeline.py
   (flow definition)           (runtime engine)
          |                          |
          v                          v
Search -> Summariser -> Fact Checker -> Writer
```

- `graph.py` is the wiring diagram.
- `pipeline.py` is the machine that executes the wiring and reports progress.

The API layer in `backend/main.py` accepts a research request, invokes the pipeline service, and returns the final report and sources.

## Project structure

- `backend/`
  - `main.py` — FastAPI application and API endpoint definitions
  - `pipeline.py` — service-layer orchestration and SSE streaming support
  - `graph.py` — LangGraph pipeline definition and node graph
  - `config.py` — shared configuration, API clients, and constants
  - `agents/` — modular agent implementations
    - `search.py`
    - `summariser.py`
    - `fact_checker.py`
    - `writer.py`
- `frontend/` — frontend scaffold and build output

## Tech stack

- Python 3
- FastAPI
- LangGraph for agent orchestration
- Groq via `langchain-groq` for LLM interactions
- Tavily for search
- React + TypeScript + Vite + Tailwind CSS for the frontend demo
- Pydantic for request validation
- Uvicorn for the development server

## Running the project

### Backend

1. Create and activate a Python virtual environment.
2. Install backend dependencies:

```bash
cd backend
python -m pip install -r requirements.txt
```

3. Create a `.env` file with these values:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

4. Start the server:

```bash
cd backend
python main.py
```

### Frontend

1. Install frontend dependencies using Bun:

```bash
cd frontend
bun install
```

2. Start Vite:

```bash
bun run dev
```

The frontend app proxies `GET /research` and `GET /research/stream` to the backend and displays live pipeline progress.

### API endpoints

- `GET /health` — health check
- `POST /research` — run the full research pipeline and return the final report
- `GET /research/stream` — live SSE pipeline updates for frontend progress

Example request:

```json
{
  "query": "Build me a knowledge base on Python async programming"
}
```

## Response format

The `/research` endpoint returns JSON with:

- `query` — the original question
- `report` — the generated research report
- `sources` — the source documents retrieved by the search agent
- `status` — the pipeline state

## Live pipeline streaming

The backend also exposes a live pipeline stream at:

- `GET /research/stream?query=<your query>`

This endpoint emits Server-Sent Events (SSE) with stage updates for:

- `search`
- `summariser`
- `fact_checker`
- `writer`
- final `pipeline` completion

A frontend can use an `EventSource` connection to render live progress while the research pipeline executes.

## Next steps and roadmap

Planned enhancements include:

- **GitHub Agent Flow** — implement a GitHub-aware agent that can create repositories on a user's behalf and store the final report as a Markdown file. The agent will first present the report and ask for user approval; only after the user approves will it create the repo and save the report.
- **Human-in-the-loop review** — require explicit user approval or rejection before the GitHub agent creates a repository
- **Frontend integration** — build a UI that submits research tasks and displays the final report

## Notes

This repository is structured so each agent is independently testable and easy to extend. The current backend is a complete research pipeline, and the next phase will add repository-aware GitHub intelligence and human review support.