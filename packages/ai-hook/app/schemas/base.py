"""베이스 스키마 정의."""

from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    """베이스 스키마."""
    
    class Config:
        """Pydantic 설정."""
        
        from_attributes = True


T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    """페이지네이션 응답 스키마."""
    
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


class HealthResponse(BaseSchema):
    """헬스 체크 응답."""
    
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorResponse(BaseSchema):
    """에러 응답."""
    
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now) 