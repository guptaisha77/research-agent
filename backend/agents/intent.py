"""
intent.py

The Intent Detection Agent.
Its job is to analyse the user's query and classify it as either
a 'guide' or 'research' intent.

'guide'    → user wants a knowledge base, study plan, or learning guide
             (triggers GitHub repo creation option with user approval)
'research' → user wants an explanation, research report, or general information
             (no repo creation prompt)

This is the FIRST step in the pipeline — it runs before
any other agent and shapes the entire flow.
"""

from config import llm
from langchain_core.messages import HumanMessage


def intent_agent(query: str) -> dict:
    """
    Analyses the query and returns the intent.

    Example input:  "Build me a knowledge base on machine learning"
    Example output: {"agent": "intent", "status": "done", "intent": "guide"}

    Example input:  "What is retrieval augmented generation?"
    Example output: {"agent": "intent", "status": "done", "intent": "research"}
    """
    print("🧠 Intent agent analysing query...")

    prompt = f"""Classify the following query into exactly one of these two categories:

guide    → the user wants a knowledge base, study plan, learning guide,
           structured tutorial, or how-to reference they can save and refer back to
research → the user wants an explanation, research report, or general information

Rules:
- Reply with ONLY the single word: guide or research
- No punctuation, no explanation, no other words

QUERY: {query}

INTENT:"""

    response = llm.invoke([HumanMessage(content=prompt)])

    # Clean the response — strip whitespace and lowercase
    # in case the model adds extra spaces or capitalises
    intent = response.content.strip().lower()

    # Safety check — if model returns something unexpected
    # default to research so we never incorrectly prompt for a repo
    if intent not in ["guide", "research"]:
        intent = "research"

    print(f"🧠 Intent detected: {intent}")

    return {
        "agent": "intent",
        "status": "done",
        "intent": intent
    }