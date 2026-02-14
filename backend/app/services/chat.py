"""Chat service for managing conversations and messages."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import AsyncGenerator, Callable, Coroutine
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, func, desc, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConversationNotFoundError
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.services.ai import AIService

logger = logging.getLogger(__name__)


class ChatService:
    """Service for chat operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize chat service.

        Args:
            db: Database session
        """
        self.db = db
        self.ai_service = AIService()

    async def create_conversation(
        self,
        user_id: UUID,
        title: str | None = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            user_id: User ID who owns the conversation
            title: Optional conversation title

        Returns:
            Conversation: Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            title=title,
        )

        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)

        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        """
        Get a conversation by ID, verifying user ownership.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify ownership

        Returns:
            Conversation: The conversation

        Raises:
            ConversationNotFoundError: If conversation not found or doesn't belong to user
        """
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )
        conversation = result.scalar_one_or_none()

        if not conversation:
            raise ConversationNotFoundError(conversation_id=str(conversation_id))

        return conversation

    async def get_conversations(
        self,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 20,
    ) -> tuple[list[Conversation], UUID | None, bool, int]:
        """
        Get paginated conversations for a user.

        Args:
            user_id: User ID
            cursor: Cursor for pagination (last conversation ID from previous page)
            limit: Maximum number of conversations to return

        Returns:
            tuple: (conversations, next_cursor, has_more, total_count)
        """
        # Build base query with stable sort (updated_at DESC, id DESC)
        query = select(Conversation).where(
            Conversation.user_id == user_id
        ).order_by(desc(Conversation.updated_at), desc(Conversation.id))

        # Apply cursor pagination if cursor is provided
        if cursor:
            cursor_result = await self.db.execute(
                select(Conversation.updated_at, Conversation.id).where(
                    Conversation.id == cursor
                )
            )
            cursor_row = cursor_result.one_or_none()

            if cursor_row:
                cursor_updated_at, cursor_id = cursor_row
                # Use composite cursor: items after cursor in (updated_at DESC, id DESC) order
                query = query.where(
                    or_(
                        Conversation.updated_at < cursor_updated_at,
                        and_(
                            Conversation.updated_at == cursor_updated_at,
                            Conversation.id < cursor_id,
                        ),
                    )
                )

        # Fetch one more than limit to check if there are more pages
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        conversations = result.scalars().all()

        # Determine if there are more pages
        has_more = len(conversations) > limit
        if has_more:
            conversations = conversations[:limit]

        # Get next cursor
        next_cursor = conversations[-1].id if conversations and has_more else None

        # Get total count
        count_result = await self.db.execute(
            select(func.count()).select_from(Conversation).where(
                Conversation.user_id == user_id
            )
        )
        total_count = count_result.scalar_one()

        return conversations, next_cursor, has_more, total_count

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
        cursor: UUID | None = None,
        limit: int = 50,
    ) -> tuple[list[Message], UUID | None, bool]:
        """
        Get paginated messages for a conversation.

        Args:
            conversation_id: Conversation ID
            user_id: User ID to verify conversation ownership
            cursor: Cursor for pagination (last message ID from previous page)
            limit: Maximum number of messages to return

        Returns:
            tuple: (messages, next_cursor, has_more)

        Raises:
            ConversationNotFoundError: If conversation not found or doesn't belong to user
        """
        # Verify conversation ownership
        await self.get_conversation(conversation_id, user_id)

        # Build base query (chronological order)
        query = select(Message).where(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.asc())

        # Apply cursor pagination if cursor is provided
        if cursor:
            # Get the cursor message's created_at
            cursor_result = await self.db.execute(
                select(Message.created_at).where(Message.id == cursor)
            )
            cursor_created_at = cursor_result.scalar_one_or_none()

            if cursor_created_at:
                query = query.where(Message.created_at > cursor_created_at)

        # Fetch one more than limit to check if there are more pages
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Determine if there are more pages
        has_more = len(messages) > limit
        if has_more:
            messages = messages[:limit]

        # Get next cursor
        next_cursor = messages[-1].id if messages and has_more else None

        return messages, next_cursor, has_more

    async def save_message(
        self,
        conversation_id: UUID,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """
        Save a message to a conversation.

        Args:
            conversation_id: Conversation ID
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata dict

        Returns:
            Message: Created message
        """
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            metadata_=metadata or {},
        )

        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)

        return message

    async def _create_tool_executor(
        self, user_id: UUID
    ) -> Callable[[str, dict], Coroutine]:
        """
        Create a tool executor function bound to the current user and DB session.

        The returned callable receives a tool name and input dict, executes
        the corresponding backend operation, and returns a JSON string result.

        Args:
            user_id: The authenticated user's ID

        Returns:
            An async callable (name: str, tool_input: dict) -> str
        """

        async def execute_tool(name: str, tool_input: dict) -> str:
            """Execute a tool call from Claude and return JSON result."""

            if name == "create_task":
                return await self._tool_create_task(user_id, tool_input)

            elif name == "list_tasks":
                return await self._tool_list_tasks(user_id, tool_input)

            elif name == "complete_task":
                return await self._tool_complete_task(user_id, tool_input)

            elif name == "create_brain_entry":
                return await self._tool_create_brain_entry(user_id, tool_input)

            elif name == "search_brain":
                return await self._tool_search_brain(user_id, tool_input)

            elif name == "get_stats":
                return await self._tool_get_stats(user_id)

            elif name == "update_task":
                return await self._tool_update_task(user_id, tool_input)

            elif name == "list_brain":
                return await self._tool_list_brain(user_id, tool_input)

            elif name == "delete_task":
                return await self._tool_delete_task(user_id, tool_input)

            elif name == "breakdown_task":
                return await self._tool_breakdown_task(user_id, tool_input)

            elif name == "get_today_tasks":
                return await self._tool_get_today_tasks(user_id)

            elif name == "update_brain_entry":
                return await self._tool_update_brain_entry(user_id, tool_input)

            elif name == "delete_brain_entry":
                return await self._tool_delete_brain_entry(user_id, tool_input)

            elif name == "get_achievements":
                return await self._tool_get_achievements(user_id)

            elif name == "get_dashboard":
                return await self._tool_get_dashboard(user_id)

            elif name == "create_mentioned_item":
                return await self._tool_create_mentioned_item(user_id, tool_input)

            elif name == "get_user_settings":
                return await self._tool_get_user_settings(user_id)

            elif name == "save_observation":
                return await self._tool_save_observation(user_id, tool_input)

            elif name == "search_observations":
                return await self._tool_search_observations(user_id, tool_input)

            return json.dumps({"error": f"Unknown tool: {name}"})

        return execute_tool

    async def _tool_create_task(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the create_task tool."""
        from app.services.task import TaskService
        from app.schemas.task import TaskCreate

        task_service = TaskService(self.db)
        data = TaskCreate(
            title=tool_input["title"],
            description=tool_input.get("description"),
            priority=tool_input.get("priority", "medium"),
            tags=tool_input.get("tags"),
            estimated_minutes=tool_input.get("estimated_minutes"),
        )
        task = await task_service.create_task(user_id, data)
        await self.db.commit()

        logger.info("Tool create_task: created task '%s' for user %s", task.title, user_id)

        return json.dumps({
            "success": True,
            "task_id": str(task.id),
            "title": task.title,
            "priority": task.priority.value,
            "status": task.status.value,
        })

    async def _tool_list_tasks(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the list_tasks tool."""
        from app.services.task import TaskService

        task_service = TaskService(self.db)
        tasks, _, _, total = await task_service.get_tasks(
            user_id=user_id,
            limit=20,
            status=tool_input.get("status"),
            priority=tool_input.get("priority"),
        )
        task_list = [
            {
                "title": t.title,
                "description": (t.description[:100] + "..." if t.description and len(t.description) > 100 else t.description),
                "status": t.status.value,
                "priority": t.priority.value,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "created_at": t.created_at.isoformat(),
                "tags": t.tags,
            }
            for t in tasks
        ]

        logger.info("Tool list_tasks: returned %d tasks for user %s", len(task_list), user_id)

        return json.dumps({"total": total, "tasks": task_list})

    async def _tool_complete_task(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the complete_task tool — awards XP, updates streak, checks achievements."""
        from app.models.task import Task, TaskStatus
        from app.services.task import TaskService

        task_title = tool_input["task_title"]

        # Find task by title (case-insensitive partial match)
        result = await self.db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status != TaskStatus.DONE,
                func.lower(Task.title).contains(task_title.lower()),
            ).limit(1)
        )
        task = result.scalar_one_or_none()

        if not task:
            return json.dumps({
                "success": False,
                "error": f"Keine offene Aufgabe mit '{task_title}' gefunden",
            })

        # Use TaskService.complete_task for proper XP/streak/achievement handling
        task_service = TaskService(self.db)
        task, xp_earned, total_xp, level, level_up = await task_service.complete_task(
            task.id, user_id
        )
        await self.db.commit()

        logger.info(
            "Tool complete_task: completed task '%s' for user %s (+%d XP, Level %d%s)",
            task.title, user_id, xp_earned, level, " LEVEL UP!" if level_up else "",
        )

        result_data = {
            "success": True,
            "title": task.title,
            "xp_earned": xp_earned,
            "total_xp": total_xp,
            "level": level,
            "level_up": level_up,
            "message": f"Aufgabe erledigt! +{xp_earned} XP",
        }
        if level_up:
            result_data["message"] += f" 🎉 Level Up! Du bist jetzt Level {level}!"

        return json.dumps(result_data)

    async def _tool_create_brain_entry(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the create_brain_entry tool."""
        from app.services.brain import BrainService
        from app.schemas.brain import BrainEntryCreate

        brain_service = BrainService(self.db)
        data = BrainEntryCreate(
            title=tool_input["title"],
            content=tool_input["content"],
            tags=tool_input.get("tags"),
            entry_type="chat_extract",
        )
        entry = await brain_service.create_entry(user_id, data)
        await self.db.commit()

        logger.info("Tool create_brain_entry: created entry '%s' for user %s", entry.title, user_id)

        return json.dumps({
            "success": True,
            "entry_id": str(entry.id),
            "title": entry.title,
        })

    async def _tool_search_brain(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the search_brain tool using ILIKE text search."""
        from app.models.brain_entry import BrainEntry

        query_text = tool_input["query"]
        search_pattern = f"%{query_text}%"

        result = await self.db.execute(
            select(BrainEntry).where(
                BrainEntry.user_id == user_id,
                or_(
                    BrainEntry.title.ilike(search_pattern),
                    BrainEntry.content.ilike(search_pattern),
                ),
            ).order_by(desc(BrainEntry.updated_at)).limit(10)
        )
        entries = result.scalars().all()

        entry_list = [
            {
                "title": e.title,
                "content": (
                    e.content[:200] + "..." if len(e.content) > 200 else e.content
                ),
                "tags": e.tags,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]

        logger.info(
            "Tool search_brain: found %d entries for query '%s' (user %s)",
            len(entry_list), query_text, user_id,
        )

        return json.dumps({"total": len(entry_list), "entries": entry_list})

    async def _tool_get_stats(self, user_id: UUID) -> str:
        """Execute the get_stats tool."""
        from app.services.gamification import GamificationService

        gam_service = GamificationService(self.db)
        stats = await gam_service.get_stats(user_id)

        logger.info("Tool get_stats: retrieved stats for user %s", user_id)

        return json.dumps({
            "total_xp": stats.total_xp,
            "level": stats.level,
            "current_streak": stats.current_streak,
            "longest_streak": stats.longest_streak,
            "tasks_completed": stats.tasks_completed,
            "xp_for_next_level": stats.xp_for_next_level,
            "progress_percent": stats.progress_percent,
        })

    async def _tool_update_task(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the update_task tool. Routes status=done through complete_task for XP."""
        from app.models.task import Task, TaskStatus, TaskPriority
        from app.services.task import TaskService

        task_title = tool_input["task_title"]

        # Find task by title (case-insensitive partial match)
        result = await self.db.execute(
            select(Task).where(
                Task.user_id == user_id,
                func.lower(Task.title).contains(task_title.lower()),
            ).order_by(desc(Task.updated_at)).limit(1)
        )
        task = result.scalar_one_or_none()

        if not task:
            return json.dumps({
                "success": False,
                "error": f"Keine Aufgabe mit '{task_title}' gefunden",
            })

        # If status is being set to done, route through complete_task for XP
        if tool_input.get("status") == "done" and task.status != TaskStatus.DONE:
            task_service = TaskService(self.db)
            task, xp_earned, total_xp, level, level_up = await task_service.complete_task(
                task.id, user_id
            )
            await self.db.commit()

            logger.info(
                "Tool update_task: completed task '%s' for user %s (+%d XP)",
                task.title, user_id, xp_earned,
            )

            result_data = {
                "success": True,
                "title": task.title,
                "status": task.status.value,
                "priority": task.priority.value,
                "xp_earned": xp_earned,
                "total_xp": total_xp,
                "level": level,
                "level_up": level_up,
            }
            if level_up:
                result_data["message"] = f"Level Up! Du bist jetzt Level {level}!"
            return json.dumps(result_data)

        # Normal update (no completion)
        if "new_title" in tool_input:
            task.title = tool_input["new_title"]
        if "description" in tool_input:
            task.description = tool_input["description"]
        if "priority" in tool_input:
            task.priority = TaskPriority(tool_input["priority"])
        if "status" in tool_input:
            task.status = TaskStatus(tool_input["status"])

        await self.db.flush()
        await self.db.commit()

        logger.info("Tool update_task: updated task '%s' for user %s", task.title, user_id)

        return json.dumps({
            "success": True,
            "title": task.title,
            "status": task.status.value,
            "priority": task.priority.value,
        })

    async def _tool_list_brain(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the list_brain tool."""
        from app.models.brain_entry import BrainEntry

        limit = tool_input.get("limit", 10)

        result = await self.db.execute(
            select(BrainEntry).where(
                BrainEntry.user_id == user_id,
            ).order_by(desc(BrainEntry.updated_at)).limit(limit)
        )
        entries = result.scalars().all()

        entry_list = [
            {
                "title": e.title,
                "content": e.content[:200] + "..." if len(e.content) > 200 else e.content,
                "tags": e.tags,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]

        logger.info("Tool list_brain: returned %d entries for user %s", len(entry_list), user_id)

        return json.dumps({"total": len(entry_list), "entries": entry_list})

    async def _tool_delete_task(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the delete_task tool."""
        from app.models.task import Task
        from app.services.task import TaskService

        task_title = tool_input["task_title"]

        result = await self.db.execute(
            select(Task).where(
                Task.user_id == user_id,
                func.lower(Task.title).contains(task_title.lower()),
            ).order_by(desc(Task.updated_at)).limit(1)
        )
        task = result.scalar_one_or_none()

        if not task:
            return json.dumps({
                "success": False,
                "error": f"Keine Aufgabe mit '{task_title}' gefunden",
            })

        title = task.title
        task_service = TaskService(self.db)
        await task_service.delete_task(task.id, user_id)
        await self.db.commit()

        logger.info("Tool delete_task: deleted task '%s' for user %s", title, user_id)

        return json.dumps({
            "success": True,
            "deleted_title": title,
            "message": f"Aufgabe '{title}' geloescht.",
        })

    async def _tool_breakdown_task(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the breakdown_task tool — generates + auto-confirms subtasks."""
        from app.models.task import Task
        from app.services.task_breakdown import TaskBreakdownService
        from app.schemas.task_breakdown import BreakdownConfirmSubtask

        task_title = tool_input["task_title"]

        result = await self.db.execute(
            select(Task).where(
                Task.user_id == user_id,
                func.lower(Task.title).contains(task_title.lower()),
            ).order_by(desc(Task.updated_at)).limit(1)
        )
        task = result.scalar_one_or_none()

        if not task:
            return json.dumps({
                "success": False,
                "error": f"Keine Aufgabe mit '{task_title}' gefunden",
            })

        breakdown_service = TaskBreakdownService(self.db)

        try:
            breakdown = await breakdown_service.generate_breakdown(task.id, user_id)
        except Exception as e:
            return json.dumps({
                "success": False,
                "error": f"Breakdown fehlgeschlagen: {str(e)}",
            })

        # Auto-confirm all suggested subtasks
        confirm_subtasks = [
            BreakdownConfirmSubtask(
                title=s.title,
                description=s.description,
                estimated_minutes=s.estimated_minutes,
            )
            for s in breakdown.suggested_subtasks
        ]

        confirm_result = await breakdown_service.confirm_breakdown(
            task.id, user_id, confirm_subtasks
        )
        await self.db.commit()

        logger.info(
            "Tool breakdown_task: broke down '%s' into %d subtasks for user %s",
            task.title, len(confirm_result.created_subtasks), user_id,
        )

        subtask_list = [
            {
                "title": s.title,
                "estimated_minutes": s.estimated_minutes,
            }
            for s in confirm_result.created_subtasks
        ]

        return json.dumps({
            "success": True,
            "parent_task": task.title,
            "subtasks_created": len(subtask_list),
            "subtasks": subtask_list,
            "message": f"'{task.title}' wurde in {len(subtask_list)} Schritte aufgeteilt.",
        })

    async def _tool_get_today_tasks(self, user_id: UUID) -> str:
        """Execute the get_today_tasks tool."""
        from app.services.task import TaskService

        task_service = TaskService(self.db)
        tasks = await task_service.get_today_tasks(user_id)

        task_list = [
            {
                "title": t.title,
                "priority": t.priority.value,
                "status": t.status.value,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "estimated_minutes": t.estimated_minutes,
            }
            for t in tasks
        ]

        logger.info("Tool get_today_tasks: %d tasks for user %s", len(task_list), user_id)

        return json.dumps({"total": len(task_list), "tasks": task_list})

    async def _tool_update_brain_entry(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the update_brain_entry tool."""
        from app.models.brain_entry import BrainEntry
        from app.services.brain import BrainService
        from app.schemas.brain import BrainEntryUpdate

        entry_title = tool_input["entry_title"]

        result = await self.db.execute(
            select(BrainEntry).where(
                BrainEntry.user_id == user_id,
                func.lower(BrainEntry.title).contains(entry_title.lower()),
            ).order_by(desc(BrainEntry.updated_at)).limit(1)
        )
        entry = result.scalar_one_or_none()

        if not entry:
            return json.dumps({
                "success": False,
                "error": f"Kein Brain-Eintrag mit '{entry_title}' gefunden",
            })

        update_data = {}
        if "new_title" in tool_input:
            update_data["title"] = tool_input["new_title"]
        if "new_content" in tool_input:
            update_data["content"] = tool_input["new_content"]
        if "new_tags" in tool_input:
            update_data["tags"] = tool_input["new_tags"]

        brain_service = BrainService(self.db)
        updated = await brain_service.update_entry(
            entry.id, user_id, BrainEntryUpdate(**update_data)
        )
        await self.db.commit()

        logger.info("Tool update_brain_entry: updated '%s' for user %s", updated.title, user_id)

        return json.dumps({
            "success": True,
            "title": updated.title,
            "message": f"Brain-Eintrag '{updated.title}' aktualisiert.",
        })

    async def _tool_delete_brain_entry(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the delete_brain_entry tool."""
        from app.models.brain_entry import BrainEntry
        from app.services.brain import BrainService

        entry_title = tool_input["entry_title"]

        result = await self.db.execute(
            select(BrainEntry).where(
                BrainEntry.user_id == user_id,
                func.lower(BrainEntry.title).contains(entry_title.lower()),
            ).order_by(desc(BrainEntry.updated_at)).limit(1)
        )
        entry = result.scalar_one_or_none()

        if not entry:
            return json.dumps({
                "success": False,
                "error": f"Kein Brain-Eintrag mit '{entry_title}' gefunden",
            })

        title = entry.title
        brain_service = BrainService(self.db)
        await brain_service.delete_entry(entry.id, user_id)
        await self.db.commit()

        logger.info("Tool delete_brain_entry: deleted '%s' for user %s", title, user_id)

        return json.dumps({
            "success": True,
            "deleted_title": title,
            "message": f"Brain-Eintrag '{title}' geloescht.",
        })

    async def _tool_get_achievements(self, user_id: UUID) -> str:
        """Execute the get_achievements tool."""
        from app.services.achievement import AchievementService

        achievement_service = AchievementService(self.db)
        result = await achievement_service.get_achievements(user_id)

        achievements = [
            {
                "name": a.name,
                "description": a.description,
                "icon": a.icon,
                "category": a.category,
                "xp_reward": a.xp_reward,
                "unlocked": a.unlocked,
                "unlocked_at": a.unlocked_at.isoformat() if a.unlocked_at else None,
            }
            for a in result.achievements
        ]

        logger.info(
            "Tool get_achievements: %d/%d unlocked for user %s",
            result.unlocked_count, result.total_count, user_id,
        )

        return json.dumps({
            "total": result.total_count,
            "unlocked": result.unlocked_count,
            "achievements": achievements,
        })

    async def _tool_get_dashboard(self, user_id: UUID) -> str:
        """Execute the get_dashboard tool."""
        from app.services.dashboard import DashboardService

        dashboard_service = DashboardService(self.db)
        summary = await dashboard_service.get_summary(user_id)

        tasks = [
            {
                "title": t.title,
                "priority": t.priority,
                "status": t.status,
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "estimated_minutes": t.estimated_minutes,
            }
            for t in summary.today_tasks
        ]

        result_data = {
            "today_tasks": tasks,
            "gamification": {
                "total_xp": summary.gamification.total_xp,
                "level": summary.gamification.level,
                "streak": summary.gamification.streak,
                "progress_percent": summary.gamification.progress_percent,
            },
            "next_deadline": {
                "task_title": summary.next_deadline.task_title,
                "due_date": summary.next_deadline.due_date.isoformat(),
            } if summary.next_deadline else None,
            "active_nudges_count": summary.active_nudges_count,
            "motivational_quote": summary.motivational_quote,
        }

        logger.info("Tool get_dashboard: summary for user %s", user_id)

        return json.dumps(result_data)

    async def _tool_create_mentioned_item(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the create_mentioned_item tool."""
        from app.models.mentioned_item import MentionedItem, MentionedItemType
        from app.models.message import Message, MessageRole

        # Find the last user message in the conversation for message_id
        last_msg_result = await self.db.execute(
            select(Message).where(
                Message.conversation_id.in_(
                    select(Conversation.id).where(Conversation.user_id == user_id)
                ),
                Message.role == MessageRole.USER,
            ).order_by(desc(Message.created_at)).limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()

        if not last_msg:
            return json.dumps({
                "success": False,
                "error": "Keine User-Nachricht gefunden",
            })

        item = MentionedItem(
            user_id=user_id,
            message_id=last_msg.id,
            item_type=MentionedItemType(tool_input["item_type"]),
            content=tool_input["content"],
            extracted_data={
                "suggested_title": tool_input.get("suggested_title"),
                "priority": tool_input.get("priority"),
                "tags": tool_input.get("tags", []),
            },
        )
        self.db.add(item)
        await self.db.flush()
        await self.db.commit()

        logger.info(
            "Tool create_mentioned_item: created %s item for user %s",
            tool_input["item_type"], user_id,
        )

        return json.dumps({
            "success": True,
            "item_type": tool_input["item_type"],
            "content": tool_input["content"],
            "message": f"Item gemerkt: {tool_input['content'][:80]}",
        })

    async def _tool_get_user_settings(self, user_id: UUID) -> str:
        """Execute the get_user_settings tool."""
        from app.services.settings import SettingsService

        settings_service = SettingsService(self.db)
        settings = await settings_service.get_settings(user_id)

        logger.info("Tool get_user_settings: retrieved settings for user %s", user_id)

        return json.dumps({
            "adhs_mode": settings.adhs_mode,
            "nudge_intensity": settings.nudge_intensity,
            "auto_breakdown": settings.auto_breakdown,
            "gamification_enabled": settings.gamification_enabled,
            "focus_timer_minutes": settings.focus_timer_minutes,
            "quiet_hours_start": settings.quiet_hours_start,
            "quiet_hours_end": settings.quiet_hours_end,
            "preferred_reminder_times": settings.preferred_reminder_times,
        })

    async def _tool_save_observation(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the save_observation tool — stores as Brain entry with special tags."""
        from app.services.brain import BrainService
        from app.schemas.brain import BrainEntryCreate

        observation = tool_input["observation"]
        category = tool_input["category"]
        confidence = tool_input.get("confidence", "medium")

        tags = [
            "alice:observation",
            f"alice:obs:{category}",
            f"alice:confidence:{confidence}",
        ]

        brain_service = BrainService(self.db)
        entry = await brain_service.create_entry(
            user_id,
            BrainEntryCreate(
                title=f"Beobachtung: {category}",
                content=observation,
                entry_type="chat_extract",
                tags=tags,
            ),
        )
        await self.db.commit()

        logger.info(
            "Tool save_observation: saved %s observation for user %s",
            category, user_id,
        )

        return json.dumps({
            "success": True,
            "category": category,
            "confidence": confidence,
            "entry_id": str(entry.id),
            "message": f"Beobachtung gespeichert: {observation[:80]}",
        })

    async def _tool_search_observations(self, user_id: UUID, tool_input: dict) -> str:
        """Execute the search_observations tool — searches Brain entries with alice:observation tag."""
        from app.models.brain_entry import BrainEntry

        query_text = tool_input["query"]
        category = tool_input.get("category")
        search_pattern = f"%{query_text}%"

        # Base filter: user + observation tag
        filters = [
            BrainEntry.user_id == user_id,
            BrainEntry.tags.overlap(["alice:observation"]),
            or_(
                BrainEntry.title.ilike(search_pattern),
                BrainEntry.content.ilike(search_pattern),
            ),
        ]

        # Optional category filter
        if category:
            filters.append(BrainEntry.tags.overlap([f"alice:obs:{category}"]))

        result = await self.db.execute(
            select(BrainEntry).where(*filters)
            .order_by(desc(BrainEntry.updated_at)).limit(10)
        )
        entries = result.scalars().all()

        observations = [
            {
                "category": self._extract_observation_category(e.tags),
                "observation": e.content[:200] + "..." if len(e.content) > 200 else e.content,
                "confidence": self._extract_observation_confidence(e.tags),
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]

        logger.info(
            "Tool search_observations: found %d for query '%s' (user %s)",
            len(observations), query_text, user_id,
        )

        return json.dumps({"total": len(observations), "observations": observations})

    @staticmethod
    def _extract_observation_category(tags: list[str]) -> str:
        """Extract observation category from tags like 'alice:obs:procrastination'."""
        for tag in tags:
            if tag.startswith("alice:obs:"):
                return tag.split(":", 2)[2]
        return "unknown"

    @staticmethod
    def _extract_observation_confidence(tags: list[str]) -> str:
        """Extract confidence level from tags like 'alice:confidence:high'."""
        for tag in tags:
            if tag.startswith("alice:confidence:"):
                return tag.split(":", 2)[2]
        return "medium"

    async def _build_system_prompt(self, user_id: UUID, user_message: str = "") -> str:
        """Build a dynamic system prompt with user context."""
        from app.services.personality import PersonalityService
        from app.services.settings import SettingsService
        from app.services.gamification import GamificationService
        from app.services.task import TaskService
        from app.services.nudge import NudgeService
        from app.models.brain_entry import BrainEntry

        parts = []

        # 1. Personality
        try:
            personality_service = PersonalityService(self.db)
            personality_prompt = await personality_service.compose_system_prompt(user_id)
            parts.append(personality_prompt)
        except Exception:
            parts.append("Du bist ALICE, eine hilfreiche KI-Assistentin fuer Menschen mit ADHS.")

        # 1b. Zeitbewusstsein
        _DAY_NAMES = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
        _MONTH_NAMES = [
            "", "Januar", "Februar", "Maerz", "April", "Mai", "Juni",
            "Juli", "August", "September", "Oktober", "November", "Dezember",
        ]
        now_berlin = datetime.now(ZoneInfo("Europe/Berlin"))
        day_name = _DAY_NAMES[now_berlin.weekday()]
        month_name = _MONTH_NAMES[now_berlin.month]
        time_str = now_berlin.strftime("%H:%M")
        parts.append(
            f"## Aktuelles Datum & Uhrzeit\n"
            f"{day_name}, {now_berlin.day}. {month_name} {now_berlin.year}, "
            f"{time_str} Uhr (Europe/Berlin)"
        )

        # 1c. User Profile
        try:
            settings_service_temp = SettingsService(self.db)
            user_settings = await settings_service_temp.get_settings(user_id)
            display_name = user_settings.display_name or "unbekannt"
            parts.append(
                f"## User-Profil\n"
                f"Name: {display_name}\n\n"
                f"Du sollst den User mit Namen ansprechen wenn dieser bekannt ist! "
                f"Das schafft eine persoenliche Verbindung und motiviert."
            )
        except Exception:
            pass

        # 2. ADHS Core Competency
        parts.append(
            "## ADHS-Kernkompetenz\n"
            "Du verstehst ADHS-Herausforderungen: Prokrastination, Vergesslichkeit, "
            "Reizueberflutung, Motivationsprobleme. Du feierst kleine Erfolge, "
            "motivierst bei Rueckschlaegen und haeltst Antworten KURZ und strukturiert. "
            "Nutze Aufzaehlungen und Emojis fuer bessere Lesbarkeit."
        )

        # 3. User Settings
        try:
            settings_service = SettingsService(self.db)
            settings = await settings_service.get_settings(user_id)
            settings_text = (
                f"## User-Einstellungen\n"
                f"- ADHS-Modus: {'aktiv' if settings.adhs_mode else 'inaktiv'}\n"
                f"- Nudge-Intensitaet: {settings.nudge_intensity}\n"
                f"- Auto-Breakdown: {'ja' if settings.auto_breakdown else 'nein'}\n"
                f"- Focus-Timer: {settings.focus_timer_minutes} Min\n"
                f"- Ruhezeiten: {settings.quiet_hours_start or 'keine'} - {settings.quiet_hours_end or 'keine'}"
            )
            parts.append(settings_text)
        except Exception:
            pass

        # 4. User Progress
        try:
            gam_service = GamificationService(self.db)
            stats = await gam_service.get_stats(user_id)
            progress_text = (
                f"## User-Fortschritt\n"
                f"- Level {stats.level} | {stats.total_xp} XP | "
                f"Streak: {stats.current_streak} Tage | "
                f"{stats.tasks_completed} Tasks erledigt | "
                f"Fortschritt: {stats.progress_percent}%"
            )
            parts.append(progress_text)
        except Exception:
            pass

        # 5. Today's Tasks (max 5)
        try:
            task_service = TaskService(self.db)
            today_tasks = await task_service.get_today_tasks(user_id)
            if today_tasks:
                task_lines = []
                for t in today_tasks[:5]:
                    due = f" (bis {t.due_date.strftime('%H:%M')})" if t.due_date else ""
                    task_lines.append(f"- [{t.priority.value}] {t.title}{due}")
                tasks_text = "## Heutige Tasks\n" + "\n".join(task_lines)
                parts.append(tasks_text)
        except Exception:
            pass

        # 6. Behavioral Observations (last 5)
        try:
            obs_result = await self.db.execute(
                select(BrainEntry).where(
                    BrainEntry.user_id == user_id,
                    BrainEntry.tags.overlap(["alice:observation"]),
                ).order_by(desc(BrainEntry.updated_at)).limit(5)
            )
            observations = obs_result.scalars().all()
            if observations:
                obs_lines = []
                for o in observations:
                    cat = self._extract_observation_category(o.tags)
                    content_short = o.content[:100] + "..." if len(o.content) > 100 else o.content
                    obs_lines.append(f"- [{cat}] {content_short}")
                obs_text = "## Bekannte Verhaltensmuster\n" + "\n".join(obs_lines)
                parts.append(obs_text)
        except Exception:
            pass

        # 7. Active Nudges (max 3)
        try:
            nudge_service = NudgeService(self.db)
            nudge_list = await nudge_service.get_active_nudges(user_id)
            if nudge_list.nudges:
                nudge_lines = []
                for n in nudge_list.nudges[:3]:
                    nudge_lines.append(f"- [{n.nudge_level}] {n.message}")
                nudge_text = "## Aktive Nudges\n" + "\n".join(nudge_lines)
                parts.append(nudge_text)
        except Exception:
            pass

        # 8. Tool Usage Rules
        parts.append(
            "## KRITISCH: Tool-Nutzung\n"
            "Du MUSST die Tools IMMER tatsaechlich aufrufen! "
            "Sag NIEMALS 'Ich habe die Aufgabe als erledigt markiert' oder "
            "'Ich habe dir XP gegeben' ohne den entsprechenden Tool-Call "
            "(complete_task, create_task, etc.) TATSAECHLICH auszufuehren. "
            "Wenn du eine Aktion beschreibst, MUSS der Tool-Call vorher erfolgt sein.\n\n"
            "### Pflicht-Tools bei Aktionen:\n"
            "- User sagt Aufgabe erledigt → complete_task aufrufen\n"
            "- User will neue Aufgabe → create_task aufrufen\n"
            "- User will Info speichern → create_brain_entry aufrufen\n"
            "- User fragt nach Fortschritt → get_stats aufrufen\n\n"
            "### Allgemeine Regeln:\n"
            "1. IMMER zuerst list_tasks pruefen bevor neue Tasks erstellt werden\n"
            "2. Proaktiv Brain nutzen — wichtige Infos automatisch speichern\n"
            "3. Ueberfaellige Tasks? → Sanft nachfragen. Lange offen? → breakdown_task anbieten\n"
            "4. Bei Fragen ZUERST search_brain nutzen\n"
            "5. Demotivation erkennen → get_stats + get_achievements zeigen\n"
            "6. VERHALTEN BEOBACHTEN und via save_observation speichern:\n"
            "   - Prokrastination bei bestimmten Aufgabentypen\n"
            "   - Produktive Tageszeiten\n"
            "   - Emotionale Muster\n"
            "   - Vermeidungsverhalten\n"
            "7. Vor Ratschlaegen search_observations pruefen\n"
            "8. Beilaeufig erwaehntes via create_mentioned_item speichern\n"
            "9. User-Einstellungen (Nudge-Intensitaet, Ruhezeiten) respektieren"
        )

        # 9. Response Format
        parts.append(
            "## Antwort-Format\n"
            "- Nutze **Markdown** fuer Formatierung\n"
            "- Halte Antworten kurz (max 3-4 Absaetze)\n"
            "- Bei Task-Aktionen: Bestaetigung was du getan hast\n"
            "- Sprache: IMMER Deutsch\n"
            "- Emojis fuer Lesbarkeit nutzen"
        )

        base_prompt = "\n\n".join(parts)

        # Enrich with memory context (Phase 5)
        if user_message:
            try:
                from app.services.graphiti_client import get_graphiti_client
                from app.services.memory import MemoryService
                from app.services.context_builder import ContextBuilder

                graphiti = get_graphiti_client()
                if graphiti.enabled:
                    memory_service = MemoryService(self.db, graphiti)
                    builder = ContextBuilder(memory_service)
                    base_prompt = await builder.enrich(
                        base_prompt=base_prompt,
                        user_id=str(user_id),
                        user_message=user_message,
                    )
            except Exception:
                logger.warning("Memory enrichment failed, using base prompt")

        return base_prompt

    async def send_message_simple(
        self,
        user_id: UUID,
        conversation_id: UUID,
        content: str,
    ) -> str:
        """
        Send a message and get AI response as a simple string (non-streaming).

        This is a simplified version of the streaming flow, used by voice
        and other contexts where streaming is not needed.

        Args:
            user_id: User ID
            conversation_id: Conversation ID
            content: Message content

        Returns:
            str: AI response text
        """
        # Save user message
        await self.save_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )

        # Get conversation history for context
        messages, _, _ = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=10,  # Last 10 messages for context
        )

        # Build messages array for Claude API
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.role.value if msg.role != MessageRole.SYSTEM else "user",
                "content": msg.content,
            })

        # Create tool executor bound to current user and DB session
        tool_executor = await self._create_tool_executor(user_id)

        # Build dynamic system prompt with user context
        system_prompt = await self._build_system_prompt(user_id, user_message=content)

        # Get full response with tool use
        response_text = await self.ai_service.get_response_with_tools(
            messages=api_messages,
            system_prompt=system_prompt,
            tool_executor=tool_executor,
        )

        # Save assistant message
        await self.save_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=response_text,
        )

        # Process episode async for memory system (Phase 5)
        try:
            from app.services.graphiti_client import get_graphiti_client
            from app.services.memory import MemoryService

            graphiti = get_graphiti_client()
            if graphiti.enabled:
                messages_for_analysis = [
                    {"role": m.role.value, "content": m.content}
                    for m in messages
                ] + [
                    {"role": "user", "content": content},
                    {"role": "assistant", "content": response_text},
                ]
                asyncio.create_task(
                    self._process_episode_background(
                        graphiti, str(user_id), str(conversation_id), messages_for_analysis
                    )
                )
        except Exception:
            logger.warning("Failed to schedule episode processing")

        return response_text

    async def stream_ai_response(
        self,
        conversation_id: UUID,
        user_message: str,
        user_id: UUID,
    ) -> AsyncGenerator[str, None]:
        """
        Get AI response for a user message with tool use support.

        Internally calls Claude with tool definitions. Claude may execute
        multiple tool calls (create tasks, search brain, etc.) before
        producing a final text response. The final text is then yielded
        word-by-word to maintain SSE streaming compatibility.

        Args:
            conversation_id: Conversation ID
            user_message: User's message content
            user_id: User ID

        Yields:
            str: Text chunks for the SSE stream
        """
        # Get conversation history for context
        messages, _, _ = await self.get_messages(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=10,  # Last 10 messages for context
        )

        # Build messages array for Claude API
        api_messages = []
        for msg in messages:
            api_messages.append({
                "role": msg.role.value if msg.role != MessageRole.SYSTEM else "user",
                "content": msg.content,
            })

        # Add current user message
        api_messages.append({
            "role": "user",
            "content": user_message,
        })

        # Create tool executor bound to current user and DB session
        tool_executor = await self._create_tool_executor(user_id)

        # Build dynamic system prompt with user context
        system_prompt = await self._build_system_prompt(user_id, user_message=user_message)

        # Get full response with tool use
        response_text = await self.ai_service.get_response_with_tools(
            messages=api_messages,
            system_prompt=system_prompt,
            tool_executor=tool_executor,
        )

        # Yield word-by-word for SSE streaming effect, preserving newlines
        for line_idx, line in enumerate(response_text.split("\n")):
            if line_idx > 0:
                yield "\n"
            words = line.split(" ")
            for i, word in enumerate(words):
                if word:
                    yield word + (" " if i < len(words) - 1 else "")

        # Process episode async for memory system (Phase 5)
        try:
            from app.services.graphiti_client import get_graphiti_client

            graphiti = get_graphiti_client()
            if graphiti.enabled:
                messages_for_analysis = [
                    {"role": m.role.value, "content": m.content}
                    for m in messages
                ] + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": response_text},
                ]
                asyncio.create_task(
                    self._process_episode_background(
                        graphiti, str(user_id), str(conversation_id), messages_for_analysis
                    )
                )
        except Exception:
            logger.warning("Failed to schedule episode processing for streaming path")

    @staticmethod
    async def _process_episode_background(
        graphiti, user_id: str, conversation_id: str, messages: list[dict]
    ) -> None:
        """Process conversation episode in background with its own DB session."""
        try:
            from app.core.database import AsyncSessionLocal
            from app.services.memory import MemoryService

            async with AsyncSessionLocal() as db:
                memory_service = MemoryService(db, graphiti)
                await memory_service.process_episode(user_id, conversation_id, messages)
                await db.commit()
        except Exception:
            logger.exception("Background episode processing failed for conversation %s", conversation_id)
