"""NLP Analyzer service for conversation mood/pattern analysis.

Uses a single Claude API call per conversation to extract mood, energy,
focus scores and ADHS patterns. Called asynchronously after a conversation ends.
"""

import json
import logging
import re

import httpx

from app.core.config import settings
from app.schemas.memory import ConversationAnalysis

logger = logging.getLogger(__name__)

# ADHS-specific patterns the analyzer should detect
ADHS_PATTERNS = [
    "procrastination",
    "hyperfocus",
    "task_switching",
    "time_blindness",
    "emotional_dysregulation",
    "rejection_sensitivity",
    "dopamine_seeking",
    "working_memory_overload",
    "sleep_disruption",
    "transition_difficulty",
    "perfectionism_paralysis",
    "social_masking",
    "paralysis_by_analysis",
]

SYSTEM_PROMPT = """\
You are a clinical NLP analyzer specializing in ADHS (ADHD) coaching conversations.
Your task is to analyze a conversation between a user and their ADHS coach (ALICE) \
and extract structured data.

Respond ONLY with valid JSON. No markdown, no explanation, no extra text.

The JSON must have exactly these fields:
- "mood_score": float from -1.0 (very negative) to 1.0 (very positive)
- "energy_level": float from 0.0 (very low) to 1.0 (very high)
- "focus_score": float from 0.0 (very unfocused) to 1.0 (very focused)
- "detected_patterns": list of ADHS pattern strings detected in the conversation
- "pattern_triggers": list of strings describing what triggered the detected patterns
- "notable_facts": list of strings with notable personal facts about the user

For detected_patterns, only use these values:
procrastination, hyperfocus, task_switching, time_blindness, \
emotional_dysregulation, rejection_sensitivity, dopamine_seeking, \
working_memory_overload, sleep_disruption, transition_difficulty, \
perfectionism_paralysis, social_masking, paralysis_by_analysis

If no patterns are detected, return empty lists. Be conservative — only flag \
patterns you are confident about based on the conversation content.\
"""


def _neutral_analysis() -> ConversationAnalysis:
    """Return a neutral ConversationAnalysis with default values."""
    return ConversationAnalysis(
        mood_score=0.0,
        energy_level=0.5,
        focus_score=0.5,
        detected_patterns=[],
        pattern_triggers=[],
        notable_facts=[],
    )


class NLPAnalyzer:
    """Analyzes conversations using Claude to extract mood, energy, focus and ADHS patterns."""

    def __init__(self) -> None:
        """Initialize the NLP analyzer with API settings."""
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-haiku-4-5-20251001"

    async def analyze(self, messages: list[dict]) -> ConversationAnalysis:
        """Analyze a conversation and return structured analysis.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.

        Returns:
            ConversationAnalysis with mood, energy, focus scores and patterns.
            Returns neutral values on any failure — never raises.
        """
        if not messages:
            logger.info("NLPAnalyzer: No messages to analyze, returning neutral values")
            return _neutral_analysis()

        if not self.api_key:
            logger.warning("NLPAnalyzer: No API key configured, returning neutral values")
            return _neutral_analysis()

        try:
            user_prompt = self._build_analysis_prompt(messages)

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 1024,
                        "system": SYSTEM_PROMPT,
                        "messages": [
                            {"role": "user", "content": user_prompt},
                        ],
                    },
                )

            if response.status_code != 200:
                logger.error(
                    "NLPAnalyzer: Claude API error %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return _neutral_analysis()

            result = response.json()
            content_blocks = result.get("content", [])

            # Extract text from response
            raw_text = ""
            for block in content_blocks:
                if block.get("type") == "text":
                    raw_text += block["text"]

            if not raw_text:
                logger.warning("NLPAnalyzer: Empty response from Claude API")
                return _neutral_analysis()

            return self._parse_response(raw_text)

        except Exception:
            logger.exception("NLPAnalyzer: Unexpected error during analysis")
            return _neutral_analysis()

    def _build_analysis_prompt(self, messages: list[dict]) -> str:
        """Build the user prompt with formatted conversation for analysis.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            Formatted prompt string.
        """
        formatted = self._format_messages(messages)
        return (
            "Analyze the following ADHS coaching conversation and extract:\n"
            "- mood_score (-1.0 to 1.0)\n"
            "- energy_level (0.0 to 1.0)\n"
            "- focus_score (0.0 to 1.0)\n"
            "- detected_patterns (list of ADHS pattern names)\n"
            "- pattern_triggers (list of trigger descriptions)\n"
            "- notable_facts (list of personal facts about the user)\n\n"
            "Conversation:\n"
            "---\n"
            f"{formatted}\n"
            "---\n\n"
            "Respond with valid JSON only."
        )

    def _format_messages(self, messages: list[dict]) -> str:
        """Format message dicts into readable conversation text.

        Args:
            messages: List of message dicts with 'role' and 'content'.

        Returns:
            Formatted string with 'User:' and 'ALICE:' prefixes.
        """
        lines = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "user":
                lines.append(f"User: {content}")
            elif role == "assistant":
                lines.append(f"ALICE: {content}")
            else:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    def _parse_response(self, raw: str) -> ConversationAnalysis:
        """Parse Claude's JSON response into a ConversationAnalysis.

        Strips markdown code blocks if present. Returns neutral values
        on any parse failure.

        Args:
            raw: Raw text response from Claude.

        Returns:
            ConversationAnalysis instance.
        """
        try:
            # Strip markdown code blocks (```json ... ``` or ``` ... ```)
            cleaned = raw.strip()
            match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1).strip()

            data = json.loads(cleaned)
            return ConversationAnalysis(**data)
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            logger.warning("NLPAnalyzer: Failed to parse response: %s", e)
            return _neutral_analysis()
        except Exception as e:
            logger.warning("NLPAnalyzer: Unexpected parse error: %s", e)
            return _neutral_analysis()
