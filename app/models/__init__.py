"""
Models package for database document structures.
These models represent how data is stored in MongoDB.
"""
from .product import ProductDocument, ProductAttribute, ProductIndex
from .order import (
    OrderDocument, 
    OrderItemDocument, 
    ShippingAddress, 
    OrderStatusHistory
)

__all__ = [
    # Product models
    "ProductDocument",
    "ProductAttribute", 
    "ProductIndex",
    
    # Order models
    "OrderDocument",
    "OrderItemDocument",
    "ShippingAddress", 
    "OrderStatusHistory"
]