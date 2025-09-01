"""
Pagination type definitions and utilities.
Standardizes pagination across all list endpoints.
"""

from typing import Optional, List, TypeVar, Generic
from pydantic import BaseModel, Field, field_validator
from app.shared.constants.http import APIConstants

T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Standardized pagination parameters for list endpoints.
    Validates and normalizes pagination inputs.
    """
    page: int = Field(
        default=APIConstants.DEFAULT_PAGE,
        ge=1,
        description="Page number (1-based)"
    )
    size: int = Field(
        default=APIConstants.DEFAULT_PAGE_SIZE,
        ge=APIConstants.MIN_PAGE_SIZE,
        le=APIConstants.MAX_PAGE_SIZE,
        description="Number of items per page"
    )
    
    @field_validator('page')
    @classmethod
    def validate_page(cls, v):
        """Ensure page is at least 1"""
        if v < 1:
            return 1
        return v
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v):
        """Ensure size is within allowed bounds"""
        if v < APIConstants.MIN_PAGE_SIZE:
            return APIConstants.MIN_PAGE_SIZE
        if v > APIConstants.MAX_PAGE_SIZE:
            return APIConstants.MAX_PAGE_SIZE
        return v
    
    @property
    def offset(self) -> int:
        """Calculate offset for database queries"""
        return (self.page - 1) * self.size
    
    @property
    def limit(self) -> int:
        """Get limit for database queries"""
        return self.size


class SortParams(BaseModel):
    """
    Standardized sorting parameters for list endpoints.
    """
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort order: 'asc' or 'desc'"
    )
    
    @field_validator('sort_order')
    @classmethod
    def validate_sort_order(cls, v):
        """Normalize sort order"""
        return v.lower()


class FilterParams(BaseModel):
    """
    Base class for filter parameters.
    Can be extended for specific endpoint filtering needs.
    """
    search: Optional[str] = Field(None, description="Search query")
    
    @field_validator('search')
    @classmethod
    def validate_search(cls, v):
        """Clean and validate search query"""
        if v:
            return v.strip()
        return v


class PaginatedResult(BaseModel, Generic[T]):
    """
    Result container for paginated queries.
    Contains both data and pagination metadata.
    """
    items: List[T] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Items per page")
    
    @property
    def total_pages(self) -> int:
        """Calculate total number of pages"""
        if self.total == 0:
            return 1
        return (self.total + self.size - 1) // self.size
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next page"""
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page"""
        return self.page > 1
    
    @property
    def start_index(self) -> int:
        """Get the starting index of items on current page (1-based)"""
        if self.total == 0:
            return 0
        return (self.page - 1) * self.size + 1
    
    @property
    def end_index(self) -> int:
        """Get the ending index of items on current page (1-based)"""
        if self.total == 0:
            return 0
        end = self.page * self.size
        return min(end, self.total)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for API response"""
        return {
            "items": [item.dict() if hasattr(item, 'dict') else item for item in self.items],
            "pagination": {
                "total": self.total,
                "page": self.page,
                "size": self.size,
                "total_pages": self.total_pages,
                "has_next": self.has_next,
                "has_prev": self.has_prev,
                "start_index": self.start_index,
                "end_index": self.end_index
            }
        }


class ContestFilterParams(FilterParams):
    """
    Contest-specific filter parameters.
    Extends base FilterParams with contest-related filters.
    """
    status: Optional[str] = Field(None, description="Filter by contest status")
    location: Optional[str] = Field(None, description="Filter by location")
    creator_id: Optional[int] = Field(None, description="Filter by creator ID")
    sponsor_id: Optional[int] = Field(None, description="Filter by sponsor ID")
    active_only: bool = Field(False, description="Show only active contests")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        """Validate contest status"""
        if v:
            from app.shared.constants.contest import ContestConstants
            if v not in ContestConstants.VALID_STATUSES:
                raise ValueError(f"Invalid status. Must be one of: {ContestConstants.VALID_STATUSES}")
        return v


class UserFilterParams(FilterParams):
    """
    User-specific filter parameters.
    """
    role: Optional[str] = Field(None, description="Filter by user role")
    verified_only: bool = Field(False, description="Show only verified users")
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v):
        """Validate user role"""
        if v:
            from app.shared.constants.auth import AuthConstants
            if v not in AuthConstants.VALID_ROLES:
                raise ValueError(f"Invalid role. Must be one of: {AuthConstants.VALID_ROLES}")
        return v


def create_paginated_result(
    items: List[T],
    total: int,
    pagination: PaginationParams
) -> PaginatedResult[T]:
    """
    Helper function to create a PaginatedResult from query results.
    
    Args:
        items: List of items for current page
        total: Total number of items across all pages
        pagination: Pagination parameters used for the query
    
    Returns:
        PaginatedResult with items and metadata
    """
    return PaginatedResult(
        items=items,
        total=total,
        page=pagination.page,
        size=pagination.size
    )
