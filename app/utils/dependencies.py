"""
FastAPI dependencies for database access and common validations
"""
from fastapi import HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# This will be imported from config.database
database = None


async def get_database() -> AsyncIOMotorDatabase:
    """
    Dependency to get database instance
    
    Returns:
        AsyncIOMotorDatabase instance
        
    Raises:
        HTTPException: If database connection is not available
    """
    if database is None:
        raise HTTPException(
            status_code=503, 
            detail="Database connection not available. Please check your MongoDB connection."
        )
    return database


def validate_object_id(object_id: str, resource_name: str = "resource") -> ObjectId:
    """
    Validate and convert string to ObjectId
    
    Args:
        object_id: String representation of ObjectId
        resource_name: Name of the resource for error messages
        
    Returns:
        Valid ObjectId instance
        
    Raises:
        HTTPException: If ObjectId format is invalid
    """
    if not ObjectId.is_valid(object_id):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid {resource_name} ID format: {object_id}"
        )
    return ObjectId(object_id)


async def verify_product_exists(product_id: str, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Verify that a product exists in the database
    
    Args:
        product_id: Product ID to verify
        db: Database instance
        
    Returns:
        Product document if found
        
    Raises:
        HTTPException: If product is not found or ID is invalid
    """
    object_id = validate_object_id(product_id, "product")
    
    product = await db.products.find_one({"_id": object_id})
    if not product:
        raise HTTPException(
            status_code=404, 
            detail=f"Product {product_id} not found"
        )
    
    return product


async def verify_order_exists(order_id: str, db: AsyncIOMotorDatabase) -> Dict[str, Any]:
    """
    Verify that an order exists in the database
    
    Args:
        order_id: Order ID to verify
        db: Database instance
        
    Returns:
        Order document if found
        
    Raises:
        HTTPException: If order is not found or ID is invalid
    """
    object_id = validate_object_id(order_id, "order")
    
    order = await db.orders.find_one({"_id": object_id})
    if not order:
        raise HTTPException(
            status_code=404, 
            detail=f"Order {order_id} not found"
        )
    
    return order


async def verify_products_exist(product_ids: list[str], db: AsyncIOMotorDatabase) -> Dict[str, Dict[str, Any]]:
    """
    Verify that multiple products exist in the database
    
    Args:
        product_ids: List of product IDs to verify
        db: Database instance
        
    Returns:
        Dictionary mapping product_id -> product document
        
    Raises:
        HTTPException: If any product is not found or has invalid ID format
    """
    # Validate all product IDs first
    object_ids = []
    for product_id in product_ids:
        object_ids.append(validate_object_id(product_id, "product"))
    
    # Fetch all products in a single query
    cursor = db.products.find({"_id": {"$in": object_ids}})
    found_products = await cursor.to_list(length=None)
    
    # Create mapping of string ID to product document
    product_map = {str(product["_id"]): product for product in found_products}
    
    # Check if all products were found
    missing_products = set(product_ids) - set(product_map.keys())
    if missing_products:
        raise HTTPException(
            status_code=404,
            detail=f"Products not found: {', '.join(missing_products)}"
        )
    
    return product_map


def validate_pagination_params(limit: int, offset: int) -> tuple[int, int]:
    """
    Validate pagination parameters
    
    Args:
        limit: Number of items to return
        offset: Number of items to skip
        
    Returns:
        Tuple of validated (limit, offset)
        
    Raises:
        HTTPException: If pagination parameters are invalid
    """
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="Offset must be non-negative"
        )
    
    return limit, offset


# Dependency functions for route injection
async def get_db() -> AsyncIOMotorDatabase:
    """Alias for get_database for shorter dependency injection"""
    return await get_database()