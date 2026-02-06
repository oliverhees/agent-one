"""AI service for interacting with Claude API."""

import os
from typing import AsyncGenerator

import httpx

from app.core.config import settings
from app.core.exceptions import AIServiceUnavailableError


class AIService:
    """Service for AI interactions using Claude API."""

    def __init__(self):
        """Initialize AI service."""
        self.api_key = settings.anthropic_api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-3-5-sonnet-20241022"

    async def stream_response(
        self,
        messages: list[dict],
        system_prompt: str = "You are ALICE, a helpful AI assistant.",
    ) -> AsyncGenerator[str, None]:
        """
        Stream response from Claude API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: System prompt for the AI

        Yields:
            str: Streamed text chunks

        Raises:
            AIServiceUnavailableError: If API is unavailable or returns error
        """
        # If no API key is set, return mock response for development
        if not self.api_key:
            mock_response = "Hello! I'm ALICE, your AI assistant. (Mock mode - no API key configured)"
            for word in mock_response.split():
                yield word + " "
            return

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 4096,
                        "system": system_prompt,
                        "messages": messages,
                        "stream": True,
                    },
                ) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        raise AIServiceUnavailableError(
                            detail=f"Claude API error: {response.status_code} - {error_text.decode()}"
                        )

                    async for line in response.aiter_lines():
                        if not line:
                            continue

                        # Claude API uses SSE format with "data: " prefix
                        if line.startswith("data: "):
                            data = line[6:]  # Remove "data: " prefix

                            # Skip event type markers
                            if data in ["[DONE]", "{}"]:
                                continue

                            # Parse JSON and extract text delta
                            try:
                                import json
                                event = json.loads(data)

                                # Handle content_block_delta events
                                if event.get("type") == "content_block_delta":
                                    delta = event.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        text = delta.get("text", "")
                                        if text:
                                            yield text

                            except json.JSONDecodeError:
                                # Skip invalid JSON
                                continue

        except httpx.RequestError as e:
            raise AIServiceUnavailableError(
                detail=f"Failed to connect to Claude API: {str(e)}"
            )
        except Exception as e:
            raise AIServiceUnavailableError(
                detail=f"Unexpected error: {str(e)}"
            )
