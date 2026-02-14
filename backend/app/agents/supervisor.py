"""LangGraph Supervisor — central orchestration graph for ALICE agents."""

import asyncio
import logging
from typing import Any

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.agents.state import AgentState
from app.core.config import settings

logger = logging.getLogger(__name__)

AGENT_TYPES = ["email", "calendar", "research", "briefing"]

ROUTING_PROMPT = """Du bist der ALICE Supervisor. Analysiere die User-Nachricht und entscheide:

1. Braucht es einen Sub-Agent? Wenn ja, welchen?
   - "email": Fuer alles rund um Emails (lesen, schreiben, senden)
   - "calendar": Fuer Termine und Kalender-Operationen
   - "research": Fuer Web-Recherche und Informationssuche
   - "briefing": Fuer Tagesbriefings und Brain Dump Zusammenfassungen
   - "direct": Fuer direkte Antworten ohne Agent (Chat, Aufgaben, Brain, etc.)

2. Wenn ein Agent noetig ist, welche Aktion soll er ausfuehren?

Antworte NUR mit JSON:
{"agent": "email|calendar|research|briefing|direct", "action": "action_name", "reason": "kurze Begruendung"}
"""


async def safe_node(node_fn, state: AgentState, timeout_s: float, agent_name: str) -> dict:
    """
    Wrapper for agent nodes with timeout and error handling.

    Args:
        node_fn: The async node function to execute
        state: Current agent state
        timeout_s: Timeout in seconds
        agent_name: Name of the agent for logging

    Returns:
        Updated state dict or error state
    """
    try:
        result = await asyncio.wait_for(node_fn(state), timeout=timeout_s)
        return result
    except asyncio.TimeoutError:
        logger.error("%s timed out after %ss", agent_name, timeout_s)
        return {"error": f"{agent_name} Timeout nach {timeout_s}s", "current_agent": None, "next_agent": None}
    except Exception as e:
        logger.error("%s failed: %s", agent_name, e)
        return {"error": f"{agent_name} Fehler: {str(e)}", "current_agent": None, "next_agent": None}


def build_supervisor_graph() -> StateGraph:
    """
    Build the main supervisor graph that orchestrates all agents.

    The supervisor:
    1. Loads context (memory, preferences)
    2. Routes to appropriate agent or direct response
    3. Aggregates results and generates final response

    Returns:
        StateGraph instance (not yet compiled)
    """
    from app.agents.nodes.email_agent import email_agent_node
    from app.agents.nodes.calendar_agent import calendar_agent_node
    from app.agents.nodes.research_agent import research_agent_node
    from app.agents.nodes.briefing_agent import briefing_agent_node

    llm = ChatAnthropic(
        model="claude-sonnet-4-5-20250929",
        api_key=settings.anthropic_api_key,
        max_tokens=4096,
    )

    async def context_loader(state: AgentState) -> dict:
        """
        Load user context before routing.

        TODO (Phase 6):
        - Load memory context from Graphiti
        - Load user preferences from database
        - Load recent conversation history

        Args:
            state: Current agent state

        Returns:
            State update with current_agent set
        """
        return {"current_agent": "supervisor"}

    async def supervisor_node(state: AgentState) -> dict:
        """
        Main supervisor node that analyzes user request and routes to agents.

        Args:
            state: Current agent state

        Returns:
            State update with routing decision
        """
        import json as json_mod

        messages = state["messages"]
        system = state.get("system_prompt", "Du bist ALICE.")

        routing_messages = [
            SystemMessage(content=ROUTING_PROMPT + "\n\n" + system),
            *messages[-5:],
        ]

        response = await llm.ainvoke(routing_messages)
        text = response.content if isinstance(response.content, str) else str(response.content)

        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            decision = json_mod.loads(text[start:end])
            agent = decision.get("agent", "direct")
            action = decision.get("action", "")
        except (ValueError, json_mod.JSONDecodeError):
            agent = "direct"
            action = ""

        if agent == "direct" or agent not in AGENT_TYPES:
            return {"next_agent": None, "current_agent": None, "pending_action": None}

        return {
            "next_agent": agent,
            "current_agent": agent,
            "pending_action": {"agent": agent, "action": action},
        }

    async def direct_response(state: AgentState) -> dict:
        """
        Generate direct response without specialized agent.

        Used for:
        - General chat
        - Task management
        - Brain entries
        - Simple questions

        Args:
            state: Current agent state

        Returns:
            State update with AI response message
        """
        messages = state["messages"]
        system = state.get("system_prompt", "Du bist ALICE.")
        response = await llm.ainvoke([SystemMessage(content=system)] + messages)
        return {"messages": [response], "next_agent": None, "current_agent": None}

    async def response_node(state: AgentState) -> dict:
        """
        Final response aggregation node.

        Summarizes agent results and generates final user-facing message.

        Args:
            state: Current agent state with results

        Returns:
            State update with final response message
        """
        results = state.get("agent_results", [])
        error = state.get("error")

        if error:
            return {"messages": [AIMessage(content=f"Es gab ein Problem: {error}")]}

        if not results:
            return await direct_response(state)

        result_text = "\n".join(
            f"- {r.get('agent', '?')}: {r.get('summary', r.get('result', '?'))}"
            for r in results
        )
        summary_messages = [
            SystemMessage(content=state.get("system_prompt", "Du bist ALICE.")),
            *state["messages"],
            HumanMessage(content=f"[SYSTEM] Agent-Ergebnisse:\n{result_text}\n\nFasse die Ergebnisse fuer den User zusammen."),
        ]
        response = await llm.ainvoke(summary_messages)
        return {"messages": [response]}

    async def email_node(state):
        return await safe_node(email_agent_node, state, 30.0, "Email-Agent")

    async def calendar_node(state):
        return await safe_node(calendar_agent_node, state, 15.0, "Calendar-Agent")

    async def research_node(state):
        return await safe_node(research_agent_node, state, 20.0, "Research-Agent")

    async def briefing_node(state):
        return await safe_node(briefing_agent_node, state, 15.0, "Briefing-Agent")

    graph = StateGraph(AgentState)
    graph.add_node("context_loader", context_loader)
    graph.add_node("supervisor", supervisor_node)
    graph.add_node("direct_response", direct_response)
    graph.add_node("response_node", response_node)
    graph.add_node("email", email_node)
    graph.add_node("calendar", calendar_node)
    graph.add_node("research", research_node)
    graph.add_node("briefing", briefing_node)

    graph.add_edge(START, "context_loader")
    graph.add_edge("context_loader", "supervisor")

    def route_supervisor(state: AgentState) -> str:
        """
        Routing function to decide next node based on supervisor decision.

        Args:
            state: Current agent state

        Returns:
            Next node name
        """
        next_agent = state.get("next_agent")
        if next_agent and next_agent in AGENT_TYPES:
            return next_agent
        return "direct_response"

    graph.add_conditional_edges(
        "supervisor",
        route_supervisor,
        {
            "email": "email",
            "calendar": "calendar",
            "research": "research",
            "briefing": "briefing",
            "direct_response": "direct_response",
        },
    )

    for agent in AGENT_TYPES:
        graph.add_edge(agent, "response_node")

    graph.add_edge("direct_response", "response_node")
    graph.add_edge("response_node", END)

    return graph


def create_agent(checkpointer=None):
    """
    Create and compile the supervisor agent graph.

    Args:
        checkpointer: Optional LangGraph checkpointer for state persistence
                     Defaults to MemorySaver if not provided

    Returns:
        Compiled LangGraph agent
    """
    graph = build_supervisor_graph()
    if checkpointer is None:
        checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
