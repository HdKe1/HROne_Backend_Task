"""
Order API schemas for request/response validation.
These models define the structure of data sent to and from the API.
"""
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from bson import ObjectId


# Request Schemas

class OrderItemRequest(BaseModel):
    """Request schema for order items - HROne Task Specification."""
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, le=100, description="Quantity ordered (max 100)")
    
    @validator('product_id')
    def validate_product_id(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid product ID format')
        return v


class CreateOrderRequest(BaseModel):
    """Request schema for creating a new order - HROne Task Specification."""
    user_id: str = Field(..., min_length=1, description="User ID placing the order")
    items: List[OrderItemRequest] = Field(..., min_items=1, max_items=50, description="List of items in the order")


class UpdateOrderStatusRequest(BaseModel):
    """Request schema for updating order status."""
    status: str = Field(..., description="New order status")
    reason: Optional[str] = Field(None, description="Reason for status change")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v.lower()


class OrderQueryParams(BaseModel):
    """Query parameters for order filtering and pagination."""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    status: Optional[str] = Field(None, description="Filter by order status")
    limit: int = Field(10, ge=1, le=100, description="Number of orders to return")
    offset: int = Field(0, ge=0, description="Number of orders to skip")


# Response Schemas

class OrderItemResponse(BaseModel):
    """Response schema for order items."""
    product_id: str = Field(..., description="Product ID")
    product_name: Optional[str] = Field(None, description="Product name")
    quantity: int = Field(..., description="Quantity ordered")
    price_per_item: Optional[float] = Field(None, description="Price per item at time of order")
    total_price: Optional[float] = Field(None, description="Total price for this item")


class ShippingAddressResponse(BaseModel):
    """Response schema for shipping address."""
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State/Province")
    postal_code: Optional[str] = Field(None, description="Postal/ZIP code")
    country: Optional[str] = Field(None, description="Country")
    phone: Optional[str] = Field(None, description="Contact phone number")


class OrderResponse(BaseModel):
    """Response schema for a single order."""
    id: str = Field(..., alias="_id", description="Order ID")
    user_id: str = Field(..., description="User ID who placed the order")
    items: List[OrderItemResponse] = Field(..., description="Order items")
    total_amount: float = Field(..., description="Total order amount")
    status: str = Field(..., description="Order status")
    shipping_address: Optional[ShippingAddressResponse] = Field(None, description="Shipping address")
    payment_method: Optional[str] = Field(None, description="Payment method")
    created_at: datetime = Field(..., description="Order creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    actual_delivery: Optional[datetime] = Field(None, description="Actual delivery date")

    class Config:
        allow_population_by_field_name = True


class OrderSummaryResponse(BaseModel):
    """Simplified order response for lists."""
    id: str = Field(..., alias="_id", description="Order ID")
    user_id: str = Field(..., description="User ID")
    total_amount: float = Field(..., description="Total order amount")
    status: str = Field(..., description="Order status")
    created_at: datetime = Field(..., description="Order creation timestamp")
    
    class Config:
        allow_population_by_field_name = True


class OrdersListResponse(BaseModel):
    """Response schema for order list with pagination."""
    orders: List[OrderSummaryResponse] = Field(..., description="List of orders")
    total: int = Field(..., description="Total number of orders matching filters")
    limit: int = Field(..., description="Number of orders returned")
    offset: int = Field(..., description="Number of orders skipped")
    user_id: Optional[str] = Field(None, description="User ID filter applied")
    has_more: bool = Field(..., description="Whether there are more orders available")


class OrderCreatedResponse(BaseModel):
    """Response schema for successful order creation."""
    id: str = Field(..., alias="_id", description="Created order ID")
    user_id: str = Field(..., description="User ID")
    items: List[OrderItemResponse] = Field(..., description="Order items")
    total_amount: float = Field(..., description="Total order amount")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        allow_population_by_field_name = True


# Error Response Schemas

class ValidationErrorDetail(BaseModel):
    """Individual validation error detail."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")
    input_value: Any = Field(..., description="Value that caused the error")


class ValidationErrorResponse(BaseModel):
    """Response schema for validation errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    details: List[ValidationErrorDetail] = Field(..., description="Detailed validation errors")