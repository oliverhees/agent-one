"""Briefing sub-agent node for LangGraph."""

import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

BRIEFING_SYSTEM_PROMPT = """Du bist der ALICE Briefing-Agent. Du erstellst Tagesbriefings und Brain Dump Zusammenfassungen.

Verfuegbare Aktionen:
- generate_briefing: Tagesbriefing mit Terminen, Tasks und Tipps erstellen
- get_brain_dump_summary: Brain Dump Eintraege zusammenfassen

Antworte immer auf Deutsch. ADHS-freundlich: kurz, klar, motivierend.
"""


async def briefing_agent_node(state: AgentState) -> dict:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )
    action = state.get("pending_action", {})
    messages = [SystemMessage(content=BRIEFING_SYSTEM_PROMPT), *state["messages"][-3:]]
    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "briefing", "action": action.get("action", "generate_briefing"),
            "summary": result_text[:200], "result": result_text,
        }],
        "current_agent": None, "next_agent": None,
        "pending_action": {**action, "type": "read"},
    }
