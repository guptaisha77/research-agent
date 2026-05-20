"""
writer.py

This is the Writer Agent.
Its job is to take everything — the original query, the summary,
the fact check result, and the original sources — and compose
a clean, well-structured final report for the user.

This is the FOURTH and final agent in our pipeline.
Its output is what gets streamed to the frontend.
"""

from config import llm
from langchain_core.messages import HumanMessage


def writer_agent(query: str, summary: str, fact_check: str, sources: list) -> dict:
    """
    Takes the original query, summary, fact check result and sources.
    Returns a final structured report.

    Example input:  query="what is RAG", summary="...", fact_check="...", sources=[...]
    Example output: {"agent": "writer", "status": "done", "report": "..."}
    """
    print("✍️  Writer agent composing final report...")

    # Build a numbered citations list from the original sources
    citations = "\n".join([
        f"[{i+1}] {s['title']} - {s['url']}"
        for i, s in enumerate(sources)
    ])

    prompt = f"""You are a research report writer.
Using the summary and fact check notes below, write a clear,
well-structured research report answering the user's question.

Format the report with:
- A short introduction
- Key findings (use bullet points)
- A conclusion
- Sources listed at the bottom

QUESTION: {query}

SUMMARY: {summary}

FACT CHECK NOTES: {fact_check}

SOURCES:
{citations}

REPORT:"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "agent": "writer",
        "status": "done",
        "report": response.content,
        "sources": sources
    }