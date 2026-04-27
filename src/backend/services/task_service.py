"""Service for managing marketing tasks."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from src.backend.db_models import MarketingTask
from src.backend.services.marketing_crew import MarketingCrewService
from src.shared.models import TaskStatus, TaskResult


class TaskService:
    """Service for managing marketing tasks."""

    def __init__(self):
        """Initialize the task service."""
        self.marketing_crew = MarketingCrewService()
        # Track running tasks for cancellation
        self._running_tasks: dict[str, bool] = {}

    async def create_task(
        self, db: AsyncSession, topic: str, language: Optional[str] = None
    ) -> MarketingTask:
        """Create a new marketing task."""
        task_id = str(uuid.uuid4())
        
        task = MarketingTask(
            task_id=task_id,
            topic=topic,
            status=TaskStatus.PENDING.value,
            language=language,
        )
        
        db.add(task)
        # Flush to get the ID
        await db.flush()
        # Commit the transaction
        await db.commit()
        # Refresh to ensure we have all fields
        await db.refresh(task)
        
        return task

    async def get_task(self, db: AsyncSession, task_id: str) -> Optional[MarketingTask]:
        """Get a task by ID."""
        result = await db.execute(
            select(MarketingTask).where(MarketingTask.task_id == task_id)
        )
        return result.scalar_one_or_none()

    async def execute_task_async(self, task_id: str) -> None:
        """Execute a marketing task asynchronously with its own DB session."""
        import asyncio
        from src.shared.database import AsyncSessionLocal
        
        # Create a new database session for the background task
        async with AsyncSessionLocal() as db:
            try:
                await self.execute_task(db, task_id)
            except Exception as e:
                # Log error but don't crash
                print(f"Error executing task {task_id}: {str(e)}")
                # Try to update task status to failed
                try:
                    task = await self.get_task(db, task_id)
                    if task:
                        task.status = TaskStatus.FAILED.value
                        task.error_message = f"Execution error: {str(e)}"
                        task.completed_at = datetime.now()
                        await db.commit()
                except:
                    pass

    async def execute_task(
        self, db: AsyncSession, task_id: str
    ) -> Optional[MarketingTask]:
        """Execute a marketing task."""
        task = await self.get_task(db, task_id)
        if not task:
            return None

        # Check if task was already cancelled
        if task.status == TaskStatus.CANCELLED.value:
            return task

        # Mark task as running
        self._running_tasks[task_id] = True

        # Update status to in_progress
        task.status = TaskStatus.IN_PROGRESS.value
        await db.commit()

        try:
            # Check cancellation before starting
            if not self._running_tasks.get(task_id, False):
                task.status = TaskStatus.CANCELLED.value
                task.completed_at = datetime.now()
                task.error_message = "Task was cancelled before execution"
                await db.commit()
                return task

            # Execute marketing crew
            result = self.marketing_crew.execute_marketing_task(
                topic=task.topic,
                language=task.language,
            )

            # Check if task was cancelled during execution
            if not self._running_tasks.get(task_id, False):
                task.status = TaskStatus.CANCELLED.value
                task.completed_at = datetime.now()
                task.error_message = "Task was cancelled during execution"
                await db.commit()
                self._running_tasks.pop(task_id, None)
                return task

            # Update task with results
            task.status = result.get("status", TaskStatus.FAILED.value)
            task.completed_at = datetime.now()
            task.result = str(result.get("result", ""))
            task.content_strategy = result.get("content_strategy")
            task.social_media_posts = "\n".join(result.get("social_media_posts", []))
            task.blog_outline = result.get("blog_outline")
            task.campaign_ideas = "\n".join(result.get("campaign_ideas", []))
            task.error_message = result.get("error_message")

            await db.commit()
            await db.refresh(task)

            # Remove from running tasks
            self._running_tasks.pop(task_id, None)

            return task
        except Exception as e:
            # Check if cancellation caused the exception
            if not self._running_tasks.get(task_id, False):
                task.status = TaskStatus.CANCELLED.value
                task.error_message = "Task was cancelled"
            else:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
            task.completed_at = datetime.now()
            await db.commit()
            self._running_tasks.pop(task_id, None)
            return task

    async def cancel_task(
        self, db: AsyncSession, task_id: str
    ) -> Optional[MarketingTask]:
        """Cancel a running or pending task."""
        task = await self.get_task(db, task_id)
        if not task:
            return None

        # Only cancel if task is pending or in_progress
        if task.status not in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]:
            return task

        # Mark as cancelled in running tasks
        self._running_tasks[task_id] = False

        # Update task status
        task.status = TaskStatus.CANCELLED.value
        task.completed_at = datetime.now()
        task.error_message = "Task was cancelled by user"
        await db.commit()
        await db.refresh(task)

        return task

    async def get_all_tasks(self, db: AsyncSession) -> list[MarketingTask]:
        """Get all tasks."""
        # Use explicit commit to ensure we see latest data
        result = await db.execute(select(MarketingTask).order_by(MarketingTask.created_at.desc()))
        tasks = list(result.scalars().all())
        # Refresh all tasks to ensure we have latest data
        for task in tasks:
            await db.refresh(task)
        return tasks

    async def delete_task(
        self, db: AsyncSession, task_id: str
    ) -> bool:
        """Delete a task by ID."""
        task = await self.get_task(db, task_id)
        if not task:
            return False

        # Cancel if running
        if task.status in [TaskStatus.PENDING.value, TaskStatus.IN_PROGRESS.value]:
            self._running_tasks[task_id] = False

        # Remove from running tasks
        self._running_tasks.pop(task_id, None)

        # Delete from database
        await db.execute(delete(MarketingTask).where(MarketingTask.task_id == task_id))
        await db.commit()

        return True

    def task_to_result(self, task: MarketingTask) -> TaskResult:
        """Convert database task to TaskResult model."""
        return TaskResult(
            task_id=task.task_id,
            topic=task.topic,
            status=TaskStatus(task.status),
            created_at=task.created_at,
            completed_at=task.completed_at,
            content_strategy=task.content_strategy,
            social_media_posts=task.social_media_posts.split("\n") if task.social_media_posts else None,
            blog_outline=task.blog_outline,
            campaign_ideas=task.campaign_ideas.split("\n") if task.campaign_ideas else None,
            error_message=task.error_message,
        )

