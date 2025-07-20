"""
Order data models for database documents.
These represent the actual structure of documents stored in MongoDB.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class OrderItemDocument(BaseModel):
    """Order item document model for items within an order."""
    product_id: str = Field(..., description="Product ID reference")
    quantity: int = Field(..., gt=0, le=100, description="Quantity ordered")
    
    # These fields might be populated from product lookup
    product_name: Optional[str] = Field(None, description="Product name at time of order")
    price_per_item: Optional[float] = Field(None, description="Price per item at time of order")
    total_price: Optional[float] = Field(None, description="Total price for this item")
    
    @validator('product_id')
    def validate_product_id(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid product ID format')
        return v


class ShippingAddress(BaseModel):
    """Shipping address information."""
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    country: Optional[str] = Field(None, description="Country")
    phone: Optional[str] = Field(None, description="Contact phone number")


class OrderDocument(BaseModel):
    """
    Order document model representing the MongoDB document structure.
    This matches how orders are stored in the database.
    """
    id: Optional[str] = Field(None, alias="_id", description="Order ID")
    user_id: str = Field(..., min_length=1, description="User ID who placed the order")
    items: List[OrderItemDocument] = Field(..., min_items=1, max_items=50, description="Order items")
    total_amount: float = Field(..., ge=0, description="Total order amount")
    
    # Order status and tracking
    status: str = Field(default="pending", description="Order status")
    
    # Additional order information
    shipping_address: Optional[ShippingAddress] = Field(None, description="Shipping address")
    payment_method: Optional[str] = Field(None, description="Payment method used")
    
    # Order notes and metadata
    notes: Optional[str] = Field(None, description="Order notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional order metadata")
    
    # Timestamps
    created_at: Optional[datetime] = Field(None, description="Order creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Delivery tracking
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    actual_delivery: Optional[datetime] = Field(None, description="Actual delivery date")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v.lower()
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class OrderStatusHistory(BaseModel):
    """Order status change history."""
    status: str = Field(..., description="Status value")
    timestamp: datetime = Field(..., description="When status changed")
    reason: Optional[str] = Field(None, description="Reason for status change")
    updated_by: Optional[str] = Field(None, description="Who updated the status")