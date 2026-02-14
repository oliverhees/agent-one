"""Research sub-agent node for LangGraph."""

import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

RESEARCH_SYSTEM_PROMPT = """Du bist der ALICE Research-Agent. Du hilfst dem User bei Web-Recherchen.

Verfuegbare Aktionen:
- web_search: Suche im Internet nach Informationen
- web_extract: Extrahiere Inhalte einer bestimmten Webseite
- summarize_results: Fasse Suchergebnisse ADHS-freundlich zusammen

Antworte immer auf Deutsch. Strukturiere Ergebnisse klar mit Aufzaehlungen.
"""


async def research_agent_node(state: AgentState) -> dict:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )
    action = state.get("pending_action", {})
    messages = [SystemMessage(content=RESEARCH_SYSTEM_PROMPT), *state["messages"][-3:]]
    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "research", "action": action.get("action", "web_search"),
            "summary": result_text[:200], "result": result_text,
        }],
        "current_agent": None, "next_agent": None,
        "pending_action": {**action, "type": "read"},
    }
