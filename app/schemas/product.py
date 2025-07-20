"""
Product API schemas for request/response validation.
These models define the structure of data sent to and from the API.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from ..models.product import ProductAttribute


# Request Schemas

class CreateProductRequest(BaseModel):
    """Request schema for creating a new product - HROne Task Specification."""
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    size: str = Field(..., min_length=1, max_length=50, description="Product size")
    description: Optional[str] = Field(None, description="Product description")


class UpdateProductRequest(BaseModel):
    """Request schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, min_length=10, max_length=2000, description="Product description")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    size: Optional[str] = Field(None, min_length=1, max_length=50, description="Product size")
    category: Optional[str] = Field(None, min_length=1, max_length=100, description="Product category")
    brand: Optional[str] = Field(None, min_length=1, max_length=100, description="Product brand")
    attributes: Optional[List[ProductAttribute]] = Field(None, description="Product attributes")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Stock quantity")
    images: Optional[List[str]] = Field(None, description="Product image URLs")


class ProductQueryParams(BaseModel):
    """Query parameters for product filtering and pagination."""
    name: Optional[str] = Field(None, description="Filter by product name (supports partial matching)")
    size: Optional[str] = Field(None, description="Filter by product size")
    category: Optional[str] = Field(None, description="Filter by category")
    brand: Optional[str] = Field(None, description="Filter by brand")
    min_price: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    limit: int = Field(10, ge=1, le=100, description="Number of products to return")
    offset: int = Field(0, ge=0, description="Number of products to skip")


# Response Schemas

class ProductResponse(BaseModel):
    """Response schema for a single product."""
    id: str = Field(..., alias="_id", description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    size: str = Field(..., description="Product size")
    category: Optional[str] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    attributes: List[ProductAttribute] = Field(default=[], description="Product attributes")
    stock_quantity: Optional[int] = Field(None, description="Available stock")
    images: List[str] = Field(default=[], description="Product image URLs")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        allow_population_by_field_name = True


class ProductSummaryResponse(BaseModel):
    """Simplified product response for lists."""
    id: str = Field(..., alias="_id", description="Product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    size: str = Field(..., description="Product size")
    category: Optional[str] = Field(None, description="Product category")
    brand: Optional[str] = Field(None, description="Product brand")
    
    class Config:
        allow_population_by_field_name = True


class ProductsListResponse(BaseModel):
    """Response schema for product list with pagination."""
    products: List[ProductSummaryResponse] = Field(..., description="List of products")
    total: int = Field(..., description="Total number of products matching filters")
    limit: int = Field(..., description="Number of products returned")
    offset: int = Field(..., alias="previous", description="Number of products skipped")
    has_more: bool = Field(..., description="Whether there are more products available")
    
    class Config:
        allow_population_by_field_name = True


class ProductCreatedResponse(BaseModel):
    """Response schema for successful product creation."""
    id: str = Field(..., alias="_id", description="Created product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    size: str = Field(..., description="Product size")
    description: Optional[str] = Field(None, description="Product description")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        allow_population_by_field_name = True