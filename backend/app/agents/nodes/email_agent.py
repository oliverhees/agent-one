"""Email sub-agent node for LangGraph."""

import logging

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

EMAIL_SYSTEM_PROMPT = """Du bist der ALICE Email-Agent. Du hilfst dem User mit Email-Operationen.

Verfuegbare Aktionen:
- email_read: Emails aus dem Postfach lesen und zusammenfassen
- email_draft: Einen Email-Entwurf erstellen
- email_send: Eine Email versenden
- email_reply: Auf eine Email antworten

Antworte immer auf Deutsch. Fasse Emails ADHS-freundlich zusammen (kurz, strukturiert, Kernpunkte).
"""


async def email_agent_node(state: AgentState) -> dict:
    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=2048,
    )
    action = state.get("pending_action", {})
    action_name = action.get("action", "email_read")
    messages = [SystemMessage(content=EMAIL_SYSTEM_PROMPT), *state["messages"][-3:]]
    response = await llm.ainvoke(messages)
    result_text = response.content if isinstance(response.content, str) else str(response.content)

    return {
        "agent_results": state.get("agent_results", []) + [{
            "agent": "email", "action": action_name,
            "summary": result_text[:200], "result": result_text,
        }],
        "current_agent": None, "next_agent": None,
        "pending_action": {**action, "type": "send" if "send" in action_name else "read"},
    }
