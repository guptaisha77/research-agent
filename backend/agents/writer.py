"""
writer.py

The Writer Agent.
Its job is to take everything — the original query, the summary,
the fact check result, and the original sources — and compose
a clean, well-structured final output for the user.

For 'guide' intent: produces a structured knowledge base
with beginner/intermediate/advanced sections and a study plan.

For 'research' intent: produces a clear research report
with introduction, key findings, and conclusion.

This is the FIFTH agent in our pipeline.
Its output is shown to the user and optionally saved to GitHub.
"""

from config import llm
from langchain_core.messages import HumanMessage


def writer_agent(
    query: str,
    summary: str,
    fact_check: str,
    sources: list,
    intent: str = "research"
) -> dict:
    """
    Takes the original query, summary, fact check result, sources and intent.
    Returns a final structured output tailored to the intent.

    Example input:  query="knowledge base on ML", intent="guide", ...
    Example output: {"agent": "writer", "status": "done", "report": "..."}
    """
    print("✍️  Writer agent composing final output...")

    # Build numbered citations
    citations = "\n".join([
        f"[{i+1}] {s['title']} - {s['url']}"
        for i, s in enumerate(sources)
    ])

    # Choose the output format based on intent
    if intent == "guide":
        format_instructions = """Structure the output as a knowledge base with:
- A brief overview of the topic
- Beginner — key concepts and best resources
- Intermediate — key concepts and best resources
- Advanced — key concepts and best resources
- Suggested study plan (week by week)
- Key takeaways"""
    else:
        format_instructions = """Structure the output as a research report with:
- A short introduction
- Key findings (use bullet points)
- A conclusion"""

    prompt = f"""You are an expert technical writer and educator.
Based on the research below, create a comprehensive and well structured output
that directly answers the user's query.

{format_instructions}

Use clear markdown formatting with headers and bullet points.
Be specific and practical — avoid vague generalities.

QUESTION: {query}

SUMMARY: {summary}

FACT CHECK NOTES: {fact_check}

SOURCES:
{citations}

OUTPUT:"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "agent": "writer",
        "status": "done",
        "report": response.content,
        "sources": sources
    }