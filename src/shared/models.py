"""Shared data models for the application."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Task execution status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class MarketingTaskRequest(BaseModel):
    """Request model for creating a marketing task."""

    topic: str = Field(..., description="Marketing topic to work on")
    language: Optional[str] = Field(None, description="Output language for the task")


class MarketingTaskResponse(BaseModel):
    """Response model for marketing task."""

    task_id: str = Field(..., description="Unique task identifier")
    topic: str = Field(..., description="Marketing topic")
    status: TaskStatus = Field(..., description="Current task status")
    created_at: datetime = Field(..., description="Task creation timestamp")
    result: Optional[dict] = Field(None, description="Task execution results")


class TaskResult(BaseModel):
    """Detailed task result model."""

    task_id: str
    topic: str
    status: TaskStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    content_strategy: Optional[str] = None
    social_media_posts: Optional[list[str]] = None
    blog_outline: Optional[str] = None
    campaign_ideas: Optional[list[str]] = None
    error_message: Optional[str] = None

