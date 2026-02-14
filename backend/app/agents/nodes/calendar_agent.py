"""Calendar sub-agent node for LangGraph."""

import logging
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage
from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

CALENDAR_SYSTEM_PROMPT = """Du bist der ALICE Calendar-Agent. Du verwaltest Termine fuer den User.

Verfuegbare Aktionen:
- calendar_list_events: Termine anzeigen
- calendar_create_event: Neuen Termin erstellen
- calendar_update_event: Termin aendern
- calendar_delete_event: Termin loeschen

Antworte immer auf Deutsch. Zeige Termine uebersichtlich mit Datum, Uhrzeit und Titel.
"""


async def calendar_agent_node(state: AgentState) -> dict:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )
    action = state.get("pending_action", {})
    action_name = action.get("action", "calendar_list_events")
    messages = [SystemMessage(content=CALENDAR_SYSTEM_PROMPT), *state["messages"][-3:]]
    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)
    action_type = "read" if "list" in action_name else "write"

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "calendar", "action": action_name,
            "summary": result_text[:200], "result": result_text,
        }],
        "current_agent": None, "next_agent": None,
        "pending_action": {**action, "type": action_type},
    }
