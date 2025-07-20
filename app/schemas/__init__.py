"""
Schemas package for API request/response validation.
These models define the structure of data sent to and from the API endpoints.
"""

# Product schemas
from .product import (
    CreateProductRequest,
    UpdateProductRequest,
    ProductQueryParams,
    ProductResponse,
    ProductSummaryResponse,
    ProductsListResponse,
    ProductCreatedResponse
)

# Order schemas  
from .order import (
    OrderItemRequest,
    CreateOrderRequest,
    UpdateOrderStatusRequest,
    OrderQueryParams,
    OrderItemResponse,
    ShippingAddressResponse,
    OrderResponse,
    OrderSummaryResponse,
    OrdersListResponse,
    OrderCreatedResponse,
    ValidationErrorDetail,
    ValidationErrorResponse
)

# Common schemas
from .common import (
    HealthCheckResponse,
    RootResponse,
    ErrorResponse,
    PaginationMeta,
    SuccessResponse
)

__all__ = [
    # Product schemas
    "CreateProductRequest",
    "UpdateProductRequest", 
    "ProductQueryParams",
    "ProductResponse",
    "ProductSummaryResponse",
    "ProductsListResponse",
    "ProductCreatedResponse",
    
    # Order schemas
    "OrderItemRequest",
    "CreateOrderRequest",
    "UpdateOrderStatusRequest", 
    "OrderQueryParams",
    "OrderItemResponse",
    "ShippingAddressResponse",
    "OrderResponse",
    "OrderSummaryResponse",
    "OrdersListResponse",
    "OrderCreatedResponse",
    "ValidationErrorDetail",
    "ValidationErrorResponse",
    
    # Common schemas
    "HealthCheckResponse",
    "RootResponse",
    "ErrorResponse",
    "PaginationMeta",
    "SuccessResponse"
]