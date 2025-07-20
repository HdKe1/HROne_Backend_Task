"""
Common schemas used across the API.
"""
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class HealthCheckResponse(BaseModel):
    """Response schema for health check endpoint."""
    status: str = Field(..., description="Application health status")
    database: str = Field(..., description="Database connection status")
    timestamp: str = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Application version")


class RootResponse(BaseModel):
    """Response schema for root endpoint."""
    message: str = Field(..., description="Welcome message")
    version: str = Field(..., description="API version")
    docs: str = Field(..., description="Documentation URL")
    health: str = Field(..., description="Health check URL")
    status: str = Field(..., description="Application status")
    timestamp: str = Field(..., description="Response timestamp")


class ErrorResponse(BaseModel):
    """Generic error response schema."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    timestamp: Optional[datetime] = Field(None, description="Error timestamp")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    total: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Number of items skipped")
    has_more: bool = Field(..., description="Whether there are more items")
    page: Optional[int] = Field(None, description="Current page number (if using page-based pagination)")
    total_pages: Optional[int] = Field(None, description="Total number of pages")


class SuccessResponse(BaseModel):
    """Generic success response schema."""
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")