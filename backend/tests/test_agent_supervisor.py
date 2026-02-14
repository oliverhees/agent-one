"""Tests for LangGraph supervisor graph structure."""

import pytest
from app.agents.state import AgentState
from app.agents.supervisor import build_supervisor_graph, AGENT_TYPES


def test_graph_structure():
    """Test that the supervisor graph can be built and compiled."""
    graph = build_supervisor_graph()
    compiled = graph.compile()
    assert compiled is not None


def test_agent_types_defined():
    """Test that all required agent types are defined."""
    assert "email" in AGENT_TYPES
    assert "calendar" in AGENT_TYPES
    assert "research" in AGENT_TYPES
    assert "briefing" in AGENT_TYPES
    assert len(AGENT_TYPES) == 4


def test_agent_state_fields():
    """Test that AgentState has all required fields."""
    state: AgentState = {
        "messages": [],
        "user_id": "test",
        "next_agent": None,
        "agent_plan": [],
        "trust_level": 1,
        "requires_approval": False,
        "pending_action": None,
        "agent_results": [],
        "current_agent": None,
        "error": None,
        "memory_context": None,
        "user_preferences": {},
        "system_prompt": "test",
    }
    assert state["trust_level"] == 1
    assert state["user_id"] == "test"
    assert state["messages"] == []
    assert state["agent_results"] == []
