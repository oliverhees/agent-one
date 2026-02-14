"""Agent state definition for LangGraph."""

from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """State shared across all agents in the LangGraph workflow."""

    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    next_agent: str | None
    agent_plan: list[str]
    trust_level: int
    requires_approval: bool
    pending_action: dict | None
    agent_results: list[dict]
    current_agent: str | None
    error: str | None
    memory_context: str | None
    user_preferences: dict
    system_prompt: str
