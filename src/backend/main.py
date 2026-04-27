"""FastAPI backend application."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.config import settings
from src.shared.database import engine, Base, get_db
from src.shared.models import (
    MarketingTaskRequest,
    MarketingTaskResponse,
    TaskResult,
    TaskStatus,
)
from src.backend.services.task_service import TaskService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown."""
    # Create database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Enable WAL mode for SQLite for better concurrency and transaction visibility
        from src.shared.config import settings
        from sqlalchemy import text
        if "sqlite" in settings.database_url:
            await conn.run_sync(lambda sync_conn: sync_conn.execute(text("PRAGMA journal_mode=WAL")))
    yield
    # Cleanup on shutdown
    await engine.dispose()


# Create FastAPI app
app = FastAPI(
    title="Marketing Team API",
    description="Multi-agent marketing team API using CrewAI",
    version="0.1.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize task service
task_service = TaskService()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Marketing Team API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/tasks", response_model=MarketingTaskResponse)
async def create_task(
    request: MarketingTaskRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Create a new marketing task."""
    try:
        task = await task_service.create_task(
            db=db,
            topic=request.topic,
            language=request.language,
        )
        # Task is already committed in create_task, no need to commit again
        
        # Execute task in background - create new DB session inside the task
        background_tasks.add_task(task_service.execute_task_async, task.task_id)

        return MarketingTaskResponse(
            task_id=task.task_id,
            topic=task.topic,
            status=TaskStatus(task.status),
            created_at=task.created_at,
            result=None,
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating task: {str(e)}")


@app.get("/tasks/{task_id}", response_model=TaskResult)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a task by ID."""
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_service.task_to_result(task)


@app.get("/tasks", response_model=list[TaskResult])
async def list_tasks(
    db: AsyncSession = Depends(get_db),
):
    """Get all tasks."""
    try:
        tasks = await task_service.get_all_tasks(db)
        return [task_service.task_to_result(task) for task in tasks]
    except Exception as e:
        # Log error but return empty list
        print(f"Error listing tasks: {str(e)}")
        return []


@app.post("/tasks/{task_id}/cancel", response_model=TaskResult)
async def cancel_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a running or pending task."""
    task = await task_service.cancel_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_service.task_to_result(task)


@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a task."""
    success = await task_service.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"message": "Task deleted successfully", "task_id": task_id}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.backend.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=True,
    )

