"""
config.py

Central configuration file for the project.
All shared settings, API clients, and constants are initialised here
so they can be imported across the project from a single source of truth.
"""

from langchain_groq import ChatGroq
from tavily import TavilyClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
# This must run before any os.getenv() calls
load_dotenv()

# ── LLM ────────────────────────────────────────────────────────
# Shared Groq LLM instance used by all agents
llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.1-8b-instant"
)

# ── Search ──────────────────────────────────────────────────────
# Tavily client used by the Search Agent
search_client = TavilyClient(
    api_key=os.getenv("TAVILY_API_KEY")
)

# ── Search settings ─────────────────────────────────────────────
MAX_SEARCH_RESULTS = 5       # number of sources the search agent fetches
MAX_SUMMARY_WORDS  = 200     # target length for the summariser agent
MAX_CONTENT_CHARS  = 300     # characters of each source used for fact checking