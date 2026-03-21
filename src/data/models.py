"""Core data models for the study content recommendation system"""

from datetime import datetime, date
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, field_validator


class TabAnalyticsRecord(BaseModel):
    """Record from tab_analytics table capturing browsing session data"""
    session_id: str
    hostname: str
    url: str
    category: str  # "productive", "distraction", "neutral"
    content_type: str  # "text", "video", "interactive", "audio", "mixed"
    active_seconds: int = Field(ge=0)
    timestamp: datetime

    @field_validator('category')
    @classmethod
    def validate_category(cls, v):
        valid_categories = ['productive', 'distraction', 'neutral']
        if v not in valid_categories:
            raise ValueError(f'category must be one of {valid_categories}')
        return v

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        valid_types = ['text', 'video', 'interactive', 'audio', 'mixed']
        if v not in valid_types:
            raise ValueError(f'content_type must be one of {valid_types}')
        return v


class ContentPreferenceRecord(BaseModel):
    """Daily aggregate record from content_preferences table"""
    date: date
    content_type: str
    total_time_seconds: int = Field(ge=0)
    session_count: int = Field(ge=0)
    productivity_score: float = Field(ge=0.0, le=1.0)

    @field_validator('content_type')
    @classmethod
    def validate_content_type(cls, v):
        valid_types = ['text', 'video', 'interactive', 'audio', 'mixed']
        if v not in valid_types:
            raise ValueError(f'content_type must be one of {valid_types}')
        return v


class BlogPost(BaseModel):
    """Blog post metadata and engagement metrics"""
    title: str
    url: str
    author: Optional[str] = None
    publication_date: Optional[date] = None
    source: str
    view_count: Optional[int] = Field(default=None, ge=0)
    share_count: Optional[int] = Field(default=None, ge=0)
    comment_count: Optional[int] = Field(default=None, ge=0)
    raw_html: str


class ResearchPaper(BaseModel):
    """Research paper metadata and engagement metrics"""
    title: str
    url: str
    authors: List[str]
    publication_venue: Optional[str] = None
    publication_year: Optional[int] = Field(default=None, ge=1900, le=2100)
    view_count: Optional[int] = Field(default=None, ge=0)
    citation_count: Optional[int] = Field(default=None, ge=0)
    abstract: Optional[str] = None
