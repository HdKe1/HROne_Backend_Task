"""
Product data models for database documents.
These represent the actual structure of documents stored in MongoDB.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId


class ProductAttribute(BaseModel):
    """Product attribute model for key-value pairs."""
    name: str = Field(..., min_length=1, description="Attribute name")
    value: str = Field(..., min_length=1, description="Attribute value")


class ProductDocument(BaseModel):
    """
    Product document model representing the MongoDB document structure.
    This matches how products are stored in the database.
    """
    id: Optional[str] = Field(None, alias="_id", description="Product ID")
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    
    # HROne specific fields
    size: str = Field(..., min_length=1, max_length=50, description="Product size")
    
    # Additional fields from the original code
    category: Optional[str] = Field(None, min_length=1, max_length=100, description="Product category")
    brand: Optional[str] = Field(None, min_length=1, max_length=100, description="Product brand")
    attributes: Optional[Dict[str, str]] = Field(None, description="Product attributes as key-value pairs")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    images: Optional[List[str]] = Field(None, description="List of image URLs")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ProductIndex(BaseModel):
    """Product search index fields for text search and filtering."""
    name_text: Optional[str] = None
    description_text: Optional[str] = None
    category_filter: Optional[str] = None
    brand_filter: Optional[str] = None
    size_filter: Optional[str] = None
    price_range: Optional[Dict[str, float]] = None  # {"min": 0, "max": 1000}