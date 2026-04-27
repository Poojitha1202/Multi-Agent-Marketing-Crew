"""Database models for storing tasks and results."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from src.shared.database import Base


class MarketingTask(Base):
    """Database model for marketing tasks."""

    __tablename__ = "marketing_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True, nullable=False)
    topic = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result = Column(Text, nullable=True)
    content_strategy = Column(Text, nullable=True)
    social_media_posts = Column(Text, nullable=True)
    blog_outline = Column(Text, nullable=True)
    campaign_ideas = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    language = Column(String, nullable=True)

