"""AI service for interacting with Claude API with tool use."""

import json
import logging
from typing import AsyncGenerator

import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError

logger = logging.getLogger(__name__)


# Tool definitions for Claude
ALICE_TOOLS = [
    {
        "name": "create_task",
        "description": (
            "Erstelle eine neue Aufgabe/Task fuer den Benutzer. Nutze dies wenn der User "
            "eine Aufgabe, ein To-Do, oder etwas zu erledigendes erwaehnt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Kurzer, klarer Titel der Aufgabe",
                },
                "description": {
                    "type": "string",
                    "description": "Optionale Beschreibung mit Details",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Prioritaet der Aufgabe",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags zur Kategorisierung",
                },
                "estimated_minutes": {
                    "type": "integer",
                    "description": "Geschaetzte Dauer in Minuten",
                },
            },
            "required": ["title"],
        },
    },
    {
        "name": "list_tasks",
        "description": (
            "Liste die Aufgaben des Benutzers auf. Nutze dies wenn der User "
            "nach seinen Aufgaben, To-Dos fragt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "in_progress", "done", "cancelled"],
                    "description": "Filter nach Status",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Filter nach Prioritaet",
                },
            },
        },
    },
    {
        "name": "complete_task",
        "description": (
            "Markiere eine Aufgabe als erledigt. Nutze dies wenn der User sagt, "
            "dass eine Aufgabe fertig/erledigt ist."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_title": {
                    "type": "string",
                    "description": (
                        "Titel der Aufgabe die erledigt werden soll "
                        "(wird per Textsuche gefunden)"
                    ),
                },
            },
            "required": ["task_title"],
        },
    },
    {
        "name": "create_brain_entry",
        "description": (
            "Speichere einen Eintrag im Second Brain / Wissensspeicher. Nutze dies "
            "wenn der User Notizen, Ideen, Wissen speichern moechte."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Titel des Eintrags",
                },
                "content": {
                    "type": "string",
                    "description": "Inhalt/Text des Eintrags",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags zur Kategorisierung",
                },
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "search_brain",
        "description": (
            "Durchsuche das Second Brain / den Wissensspeicher des Benutzers. "
            "Nutze dies wenn der User nach gespeichertem Wissen fragt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Suchbegriff",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_stats",
        "description": (
            "Rufe die Gamification-Statistiken ab (XP, Level, Streak, erledigte Tasks). "
            "Nutze dies wenn der User nach seinem Fortschritt fragt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "update_task",
        "description": (
            "Aktualisiere eine bestehende Aufgabe. Nutze dies um Titel, Beschreibung, "
            "Priorität oder Status zu ändern. IMMER zuerst list_tasks aufrufen um die "
            "Aufgabe zu finden, statt eine neue zu erstellen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_title": {
                    "type": "string",
                    "description": "Titel der Aufgabe die aktualisiert werden soll (Textsuche)",
                },
                "new_title": {
                    "type": "string",
                    "description": "Neuer Titel (optional)",
                },
                "description": {
                    "type": "string",
                    "description": "Neue Beschreibung (optional)",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Neue Priorität (optional)",
                },
                "status": {
                    "type": "string",
                    "enum": ["open", "in_progress", "done", "cancelled"],
                    "description": "Neuer Status (optional)",
                },
            },
            "required": ["task_title"],
        },
    },
    {
        "name": "list_brain",
        "description": (
            "Liste die neuesten Brain-Einträge des Benutzers auf. Nutze dies um zu sehen "
            "was bereits gespeichert ist, bevor du neue Einträge erstellst."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Anzahl der Einträge (Standard: 10)",
                },
            },
        },
    },
    {
        "name": "delete_task",
        "description": (
            "Loesche eine Aufgabe permanent. Nutze dies wenn der User eine Aufgabe "
            "nicht mehr braucht und loeschen moechte. ACHTUNG: Nicht rueckgaengig machbar!"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_title": {
                    "type": "string",
                    "description": "Titel der Aufgabe die geloescht werden soll (Textsuche)",
                },
            },
            "required": ["task_title"],
        },
    },
    {
        "name": "delete_all_tasks",
        "description": (
            "Loesche ALLE Aufgaben des Benutzers permanent. Nutze dies wenn der User "
            "ausdruecklich sagt, dass alle Aufgaben/Tasks geloescht werden sollen. "
            "Optional kann nach Status gefiltert werden."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["open", "in_progress", "done", "cancelled", "all"],
                    "description": "Nur Tasks mit diesem Status loeschen. 'all' loescht alle.",
                },
                "confirm": {
                    "type": "boolean",
                    "description": "Muss true sein um die Loeschung zu bestaetigen.",
                },
            },
            "required": ["confirm"],
        },
    },
    {
        "name": "breakdown_task",
        "description": (
            "Zerlege eine grosse Aufgabe in kleine, machbare Sub-Tasks (3-7 Schritte). "
            "Perfekt fuer ADHS: grosse Tasks werden ueberschaubar. Die Sub-Tasks werden "
            "automatisch als Unter-Aufgaben angelegt."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "task_title": {
                    "type": "string",
                    "description": "Titel der Aufgabe die aufgeteilt werden soll (Textsuche)",
                },
            },
            "required": ["task_title"],
        },
    },
    {
        "name": "get_today_tasks",
        "description": (
            "Zeige die heutigen Aufgaben sortiert nach Prioritaet und Deadline. "
            "Nutze dies fuer Tagesplanung und um den User an anstehende Tasks zu erinnern."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "update_brain_entry",
        "description": (
            "Aktualisiere einen bestehenden Brain-Eintrag (Titel, Inhalt oder Tags). "
            "Nutze dies wenn der User gespeicherte Informationen aendern moechte."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entry_title": {
                    "type": "string",
                    "description": "Titel des Eintrags der aktualisiert werden soll (Textsuche)",
                },
                "new_title": {
                    "type": "string",
                    "description": "Neuer Titel (optional)",
                },
                "new_content": {
                    "type": "string",
                    "description": "Neuer Inhalt (optional)",
                },
                "new_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Neue Tags (optional)",
                },
            },
            "required": ["entry_title"],
        },
    },
    {
        "name": "delete_brain_entry",
        "description": (
            "Loesche einen Brain-Eintrag permanent. Nutze dies wenn der User einen "
            "gespeicherten Eintrag nicht mehr braucht."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entry_title": {
                    "type": "string",
                    "description": "Titel des Eintrags der geloescht werden soll (Textsuche)",
                },
            },
            "required": ["entry_title"],
        },
    },
    {
        "name": "get_achievements",
        "description": (
            "Zeige alle Achievements/Erfolge mit Unlock-Status. Nutze dies wenn der User "
            "nach seinen Errungenschaften fragt oder wenn du ihn motivieren willst."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "get_dashboard",
        "description": (
            "Rufe das komplette Dashboard ab: Heutige Tasks, XP, Streak, naechste Deadline, "
            "aktive Nudges und Motivationsspruch. Perfekt fuer einen Ueberblick."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "create_mentioned_item",
        "description": (
            "Speichere ein beilaeufig erwaehnte Item aus dem Chat (Termin, Idee, Erinnerung). "
            "Nutze dies PROAKTIV wenn der User nebenbei etwas Wichtiges erwaehnt das nicht "
            "vergessen werden sollte."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "item_type": {
                    "type": "string",
                    "enum": ["task", "appointment", "idea", "follow_up", "reminder"],
                    "description": "Art des erwaehnten Items",
                },
                "content": {
                    "type": "string",
                    "description": "Extrahierter Inhalt aus dem Chat",
                },
                "suggested_title": {
                    "type": "string",
                    "description": "Vorgeschlagener Titel (optional)",
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "urgent"],
                    "description": "Vorgeschlagene Prioritaet (optional)",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags zur Kategorisierung (optional)",
                },
            },
            "required": ["item_type", "content"],
        },
    },
    {
        "name": "get_user_settings",
        "description": (
            "Lese die ADHS-Einstellungen des Users (Nudge-Intensitaet, Auto-Breakdown, "
            "Focus-Timer, Ruhezeiten). Nutze dies um dein Verhalten an die Praeferenzen "
            "des Users anzupassen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "save_observation",
        "description": (
            "Speichere eine Verhaltensbeobachtung ueber den User. Nutze dies PROAKTIV um "
            "Muster zu erkennen: Prokrastination, produktive Zeiten, emotionale Muster, "
            "Vermeidungsverhalten, Vorlieben. Diese Beobachtungen helfen dir den User "
            "besser zu unterstuetzen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "observation": {
                    "type": "string",
                    "description": "Beschreibung der Beobachtung",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "procrastination",
                        "productivity",
                        "emotional",
                        "avoidance",
                        "preference",
                    ],
                    "description": "Kategorie der Beobachtung",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Wie sicher bist du dir bei dieser Beobachtung? (Standard: medium)",
                },
            },
            "required": ["observation", "category"],
        },
    },
    {
        "name": "search_observations",
        "description": (
            "Durchsuche gespeicherte Verhaltensbeobachtungen. Nutze dies VOR Ratschlaegen "
            "um bekannte Muster zu beruecksichtigen."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Suchbegriff fuer Beobachtungen",
                },
                "category": {
                    "type": "string",
                    "enum": [
                        "procrastination",
                        "productivity",
                        "emotional",
                        "avoidance",
                        "preference",
                    ],
                    "description": "Filter nach Kategorie (optional)",
                },
            },
            "required": ["query"],
        },
    },
]


class AIService:
    """Service for AI interactions using Claude API with tool use."""

    def __init__(self):
        """Initialize AI service."""
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-sonnet-4-5-20250929"

    async def get_response_voice(
        self,
        messages: list[dict],
        system_prompt: str,
    ) -> str:
        """Fast voice response using Haiku - no tools, short output."""
        if not self.api_key:
            return "Hallo! Ich bin ALICE. (Mock-Modus)"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-haiku-4-5-20251001",
                        "max_tokens": 300,
                        "system": system_prompt,
                        "messages": messages,
                    },
                )

                if response.status_code != 200:
                    logger.error("Voice AI error: %s", response.text[:200])
                    return "Entschuldigung, ich konnte gerade nicht antworten."

                result = response.json()
                text_parts = []
                for block in result.get("content", []):
                    if block.get("type") == "text":
                        text_parts.append(block["text"])
                return "\n".join(text_parts) or "..."

        except Exception as e:
            logger.error("Voice AI error: %s", e)
            return "Entschuldigung, es gab einen Fehler."

    async def get_response_with_tools(
        self,
        messages: list[dict],
        system_prompt: str,
        tool_executor,
        model: str | None = None,
        max_tokens: int | None = None,
        max_tool_iterations: int | None = None,
        on_intermediate_text=None,
    ) -> str:
        """
        Get response from Claude with tool use support.

        Uses a non-streaming approach with a tool loop: Claude may respond with
        tool_use blocks, which are executed and fed back as tool_result messages
        until Claude returns a final text response.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System prompt for the AI
            tool_executor: Async callable (name: str, input: dict) -> str
                           that executes a tool and returns a JSON string result

        Returns:
            str: The final text response after all tool calls are resolved.

        Raises:
            AIServiceUnavailableError: If API is unavailable or returns error
        """
        if not self.api_key:
            return (
                "Hallo! Ich bin ALICE, deine KI-Assistentin. "
                "(Mock-Modus — kein API-Key konfiguriert)"
            )

        current_messages = list(messages)
        all_text_parts = []  # Collect text from ALL responses (including intermediate)
        max_iterations = max_tool_iterations or 10  # prevent infinite tool loops

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                for _ in range(max_iterations):
                    response = await client.post(
                        f"{self.base_url}/messages",
                        headers={
                            "x-api-key": self.api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json",
                        },
                        json={
                            "model": model or self.model,
                            "max_tokens": max_tokens or 4096,
                            "system": system_prompt,
                            "messages": current_messages,
                            "tools": ALICE_TOOLS,
                        },
                    )

                    if response.status_code != 200:
                        raise AIServiceUnavailableError(
                            detail=f"Claude API error: {response.status_code} - {response.text}"
                        )

                    result = response.json()
                    stop_reason = result.get("stop_reason")
                    content_blocks = result.get("content", [])

                    logger.info(
                        "Claude API response: stop_reason=%s, blocks=%d",
                        stop_reason,
                        len(content_blocks),
                    )

                    # Handle text from this response
                    if stop_reason == "tool_use" and on_intermediate_text:
                        # Tool call coming: send intermediate text immediately via callback
                        intermediate = " ".join(
                            b["text"] for b in content_blocks
                            if b.get("type") == "text" and b["text"].strip()
                        )
                        if intermediate:
                            logger.info("Intermediate text (pre-tool): '%s'", intermediate[:80])
                            await on_intermediate_text(intermediate)
                    else:
                        # Final response or no callback: collect text normally
                        for block in content_blocks:
                            if block.get("type") == "text" and block["text"].strip():
                                all_text_parts.append(block["text"])

                    # If Claude finished without requesting tools, return all text
                    if stop_reason != "tool_use":
                        final_text = " ".join(all_text_parts) or "..."
                        logger.info(
                            "Claude final response (%d chars, stop=%s)",
                            len(final_text),
                            stop_reason,
                        )
                        return final_text

                    # Handle tool_use: add assistant message, execute tools, add results
                    current_messages.append({
                        "role": "assistant",
                        "content": content_blocks,
                    })

                    tool_results = []
                    for block in content_blocks:
                        if block.get("type") == "tool_use":
                            tool_name = block["name"]
                            tool_input = block["input"]
                            tool_use_id = block["id"]

                            logger.info(
                                "Executing tool: %s with input: %s",
                                tool_name,
                                json.dumps(tool_input, ensure_ascii=False)[:200],
                            )

                            try:
                                result_str = await tool_executor(tool_name, tool_input)
                                logger.info(
                                    "Tool %s result: %s",
                                    tool_name,
                                    result_str[:200],
                                )
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": result_str,
                                })
                            except Exception as e:
                                logger.error(
                                    "Tool %s failed: %s",
                                    tool_name,
                                    str(e),
                                )
                                tool_results.append({
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": f"Fehler: {str(e)}",
                                    "is_error": True,
                                })

                    current_messages.append({
                        "role": "user",
                        "content": tool_results,
                    })

                # Max iterations reached
                return "Entschuldigung, ich konnte die Anfrage nicht abschliessen."

        except httpx.RequestError as e:
            raise AIServiceUnavailableError(
                detail=f"Failed to connect to Claude API: {str(e)}"
            )
        except AIServiceUnavailableError:
            raise
        except Exception as e:
            raise AIServiceUnavailableError(
                detail=f"Unexpected error: {str(e)}"
            )

    async def stream_response(
        self,
        messages: list[dict],
        system_prompt: str = "You are ALICE, a helpful AI assistant.",
    ) -> AsyncGenerator[str, None]:
        """
        Simple streaming without tools (legacy fallback).

        Internally calls get_response_with_tools with a no-op executor,
        then yields the response word by word to simulate streaming.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System prompt for the AI

        Yields:
            str: Streamed text chunks (word by word)

        Raises:
            AIServiceUnavailableError: If API is unavailable or returns error
        """
        response_text = await self.get_response_with_tools(
            messages=messages,
            system_prompt=system_prompt,
            tool_executor=self._noop_executor,
        )
        for word in response_text.split():
            yield word + " "

    @staticmethod
    async def _noop_executor(name: str, tool_input: dict) -> str:
        """No-op tool executor for legacy streaming mode."""
        return json.dumps({"error": "Tools not available in this context"})

    async def get_response_custom_llm(
        self,
        messages: list[dict],
        system_prompt: str,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
        max_tokens: int = 4096,
        tool_executor=None,
    ) -> str:
        """
        Get response from an OpenAI-compatible API (vLLM, Ollama, etc.).

        Supports tool use if the model handles it. Falls back to plain chat
        if tools are not supported.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System prompt for the AI
            base_url: API base URL (e.g. http://gpu-server:8000/v1)
            model: Model name (e.g. Qwen/Qwen2.5-14B-Instruct-AWQ)
            api_key: Optional API key
            max_tokens: Maximum tokens in response
            tool_executor: Optional async callable for tool execution

        Returns:
            str: The final text response
        """
        url = base_url or settings.custom_llm_base_url
        mdl = model or settings.custom_llm_model
        key = api_key or settings.custom_llm_api_key

        if not url:
            raise AIServiceUnavailableError(
                detail="Custom LLM not configured (CUSTOM_LLM_BASE_URL missing)"
            )

        # Convert to OpenAI message format (system as first message)
        openai_messages = [{"role": "system", "content": system_prompt}]
        for msg in messages:
            content = msg["content"]
            # Flatten Anthropic content blocks to plain text
            if isinstance(content, list):
                content = " ".join(
                    b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
                )
            openai_messages.append({"role": msg["role"], "content": content})

        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        # Build request body
        body: dict = {
            "model": mdl,
            "messages": openai_messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }

        # Add tools if executor provided (OpenAI tool format)
        tools_enabled = False
        if tool_executor:
            openai_tools = []
            for tool in ALICE_TOOLS:
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": tool["input_schema"],
                    },
                })
            body["tools"] = openai_tools
            tools_enabled = True

        max_iterations = 10
        all_text_parts = []

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                for _ in range(max_iterations):
                    response = await client.post(
                        f"{url}/chat/completions",
                        headers=headers,
                        json=body,
                    )

                    # If server doesn't support tool calling, retry without tools
                    if response.status_code == 400 and tools_enabled:
                        error_text = response.text
                        if "tool" in error_text.lower():
                            logger.warning(
                                "Custom LLM does not support tool calling, retrying without tools"
                            )
                            body.pop("tools", None)
                            tools_enabled = False
                            response = await client.post(
                                f"{url}/chat/completions",
                                headers=headers,
                                json=body,
                            )

                    if response.status_code != 200:
                        logger.error(
                            "Custom LLM error (%s): %s",
                            response.status_code,
                            response.text[:300],
                        )
                        raise AIServiceUnavailableError(
                            detail=f"Custom LLM error: {response.status_code}"
                        )

                    result = response.json()
                    choice = result["choices"][0]
                    message = choice["message"]
                    finish_reason = choice.get("finish_reason", "stop")

                    logger.info(
                        "Custom LLM response: model=%s, finish=%s",
                        mdl, finish_reason,
                    )

                    # Collect text content
                    if message.get("content"):
                        all_text_parts.append(message["content"])

                    # Handle tool calls (OpenAI format)
                    tool_calls = message.get("tool_calls")
                    if tool_calls and tool_executor:
                        # Add assistant message with tool calls
                        openai_messages.append(message)

                        for tc in tool_calls:
                            func = tc["function"]
                            tool_name = func["name"]
                            try:
                                tool_input = json.loads(func["arguments"])
                            except json.JSONDecodeError:
                                tool_input = {}

                            logger.info(
                                "Custom LLM tool call: %s(%s)",
                                tool_name,
                                json.dumps(tool_input, ensure_ascii=False)[:200],
                            )

                            try:
                                result_str = await tool_executor(tool_name, tool_input)
                            except Exception as e:
                                result_str = json.dumps({"error": str(e)})

                            # Add tool result
                            openai_messages.append({
                                "role": "tool",
                                "tool_call_id": tc["id"],
                                "content": result_str,
                            })

                        # Update body with new messages for next iteration
                        body["messages"] = openai_messages
                        continue

                    # No tool calls → done
                    return " ".join(all_text_parts) or "..."

                return "Entschuldigung, ich konnte die Anfrage nicht abschliessen."

        except httpx.RequestError as e:
            raise AIServiceUnavailableError(
                detail=f"Custom LLM connection failed: {str(e)}"
            )
        except AIServiceUnavailableError:
            raise
        except Exception as e:
            logger.error("Custom LLM unexpected error: %s", e, exc_info=True)
            raise AIServiceUnavailableError(
                detail=f"Custom LLM error: {str(e)}"
            )
