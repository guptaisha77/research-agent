"""
search.py

This is the Search Agent.
Its job is to take a question from the user, search the web using Tavily,
and return a clean list of relevant sources.

This is the SECOND agent that runs in our multi-agent pipeline.
It feeds its results into the Summariser agent next.
"""

from config import search_client, MAX_SEARCH_RESULTS


def search_agent(query: str) -> dict:
    """
    Takes a search query (string)
    Returns a dict with the search results
    
    Example input:  "what is retrieval augmented generation"
    Example output: {"agent": "search", "status": "done", "sources": [...]}
    """
    print(f"🔍 Search agent searching for: {query}")

    # Ask Tavily to search the web
    results = search_client.search(
        query=query,
        max_results=MAX_SEARCH_RESULTS
    )

    # Extract just the useful parts from each result
    # Tavily returns a lot of extra data we don't need
    sources = []
    for result in results["results"]:
        sources.append({
            "title": result["title"],
            "url": result["url"],
            "content": result["content"]
        })

    return {
        "agent": "search",
        "status": "done",
        "sources": sources
    }