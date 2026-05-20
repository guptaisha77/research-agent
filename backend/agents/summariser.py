"""
summariser.py

This is the Summariser Agent.
Its job is to take the raw search results from the Search Agent
and use Groq's AI to condense them into a clean, readable summary.

This is the THIRD agent that runs in our multi-agent pipeline.
It feeds its summary into the Fact Checker agent next.
"""

from config import llm, MAX_SUMMARY_WORDS
from langchain_core.messages import HumanMessage


def summariser_agent(sources: list) -> dict:
    """
    Takes a list of sources from the Search Agent
    Returns a dict with a condensed summary

    Example input:  [{"title": "...", "url": "...", "content": "..."}]
    Example output: {"agent": "summariser", "status": "done", "summary": "..."}
    """
    print(f"📄 Summariser agent reading {len(sources)} sources...")

    # Combine all source content into one big block of text
    # We join them with a separator so the AI knows where one ends
    # and the next begins
    combined_text = "\n\n---\n\n".join([
        f"Source: {s['title']}\n{s['content']}"
        for s in sources
    ])

    prompt = f"""You are a research assistant. 
Read the following sources and write a clear, concise summary.
Keep it under {MAX_SUMMARY_WORDS} words. Focus on the key facts.

SOURCES:
{combined_text}

SUMMARY:"""

    # Send the prompt to Groq and get a response
    response = llm.invoke([HumanMessage(content=prompt)])

    return {
        "agent": "summariser",
        "status": "done",
        "summary": response.content
    }