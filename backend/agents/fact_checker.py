"""
fact_checker.py

This is the Fact Checker Agent.
Its job is to look at the summary from the Summariser Agent
and cross-reference it against the original sources to check
for any inaccuracies or unsupported claims.

This is the FOURTH agent that runs in our multi-agent pipeline.
It feeds its findings into the Writer agent next.
"""

from config import llm, MAX_CONTENT_CHARS
from langchain_core.messages import HumanMessage


def fact_checker_agent(summary: str, sources: list) -> dict:
    """
    Takes the summary from the Summariser and the original sources
    Returns a dict with a verified summary and any flagged issues

    Example input:  summary="...", sources=[{...}]
    Example output: {"agent": "fact_checker", "status": "done", "verified": "...", "flags": "..."}
    """
    print("✅ Fact checker agent cross-referencing sources...")

    # Build a readable version of sources to check against
    # We only use the first MAX_CONTENT_CHARS characters of each source
    # to keep the prompt short and fast
    sources_text = "\n\n".join([
        f"- {s['title']}: {s['content'][:MAX_CONTENT_CHARS]}"
        for s in sources
    ])

    prompt = f"""You are a fact-checking assistant.
Compare the SUMMARY against the SOURCES below.
List any claims in the summary that are not supported by the sources.
If everything checks out, say "All facts verified."

SUMMARY:
{summary}

SOURCES:
{sources_text}

FACT CHECK RESULT:"""

    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "agent": "fact_checker",
        "status": "done",
        "verified": summary,
        "flags": response.content
    }