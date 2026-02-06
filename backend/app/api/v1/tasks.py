"""Task management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse, TaskCompleteResponse
from app.services.task import TaskService


router = APIRouter(tags=["Tasks"])


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    dependencies=[Depends(standard_rate_limit)],
)
async def create_task(
    data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new task for the authenticated user."""
    service = TaskService(db)
    task = await service.create_task(current_user.id, data)
    return TaskResponse.model_validate(task)


@router.get(
    "/",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List tasks",
    dependencies=[Depends(standard_rate_limit)],
)
async def list_tasks(
    cursor: UUID | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    task_status: str | None = Query(None, alias="status", description="Filter by status"),
    priority: str | None = Query(None, description="Filter by priority"),
    tags: list[str] | None = Query(None, description="Filter by tags"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of tasks for the authenticated user."""
    service = TaskService(db)
    tasks, next_cursor, has_more, total_count = await service.get_tasks(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        status=task_status,
        priority=priority,
        tags=tags,
    )

    return {
        "items": [TaskResponse.model_validate(t) for t in tasks],
        "next_cursor": str(next_cursor) if next_cursor else None,
        "has_more": has_more,
        "total_count": total_count,
    }


@router.get(
    "/today",
    response_model=list[TaskResponse],
    status_code=status.HTTP_200_OK,
    summary="Get today's tasks",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_today_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tasks due today or currently in progress for today."""
    service = TaskService(db)
    tasks = await service.get_today_tasks(current_user.id)
    return [TaskResponse.model_validate(t) for t in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific task by ID."""
    service = TaskService(db)
    task = await service.get_task(task_id, current_user.id)
    return TaskResponse.model_validate(task)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing task."""
    service = TaskService(db)
    task = await service.update_task(task_id, current_user.id, data)
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    dependencies=[Depends(standard_rate_limit)],
)
async def delete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a task."""
    service = TaskService(db)
    await service.delete_task(task_id, current_user.id)


@router.post(
    "/{task_id}/complete",
    response_model=TaskCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Complete task",
    dependencies=[Depends(standard_rate_limit)],
)
async def complete_task(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Complete a task and earn XP."""
    service = TaskService(db)
    task, xp_earned, total_xp, level, level_up = await service.complete_task(
        task_id, current_user.id
    )
    return TaskCompleteResponse(
        task=TaskResponse.model_validate(task),
        xp_earned=xp_earned,
        new_total_xp=total_xp,
        level_up=level_up,
    )
