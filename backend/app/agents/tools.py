"""Existing ALICE tools converted to LangChain tool format."""

from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession


class AliceToolkit:
    """Wrapper for existing ALICE tools to be used within LangGraph agents."""

    def __init__(self, db: AsyncSession, user_id: UUID):
        """
        Initialize the toolkit with database session and user context.

        Args:
            db: Database session for tool operations
            user_id: User ID for authorization
        """
        self.db = db
        self.user_id = user_id
        self._executor = None

    async def _get_executor(self):
        """
        Lazy-load the tool executor from ChatService.

        Returns:
            Callable tool executor function
        """
        if self._executor is None:
            from app.services.chat import ChatService

            chat_service = ChatService(self.db)
            self._executor = await chat_service._create_tool_executor(self.user_id)
        return self._executor

    async def execute(self, tool_name: str, tool_input: dict) -> str:
        """
        Execute a tool by name with given input.

        Args:
            tool_name: Name of the tool to execute
            tool_input: Tool input parameters as dict

        Returns:
            JSON string result from the tool execution
        """
        executor = await self._get_executor()
        return await executor(tool_name, tool_input)

    def get_tool_definitions(self) -> list[dict]:
        """
        Get tool definitions in Claude/Anthropic format.

        Returns:
            List of tool definition dicts
        """
        from app.services.ai import ALICE_TOOLS

        return ALICE_TOOLS
