# main.py
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import re
import os
from contextlib import asynccontextmanager

# MongoDB connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = "ecommerce_db"

# Global variables for database
database = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global database
    client = AsyncIOMotorClient(MONGODB_URL)
    database = client[DATABASE_NAME]
    
    # Create indexes for better performance
    await database.products.create_index("name")
    await database.products.create_index("attributes.size")
    await database.orders.create_index("user_id")
    await database.orders.create_index("created_at")
    
    yield
    
    # Shutdown
    client.close()

app = FastAPI(
    title="Ecommerce API",
    description="A FastAPI-based ecommerce application similar to Flipkart/Amazon",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models for request/response validation

class ProductAttribute(BaseModel):
    name: str
    value: str

class CreateProductRequest(BaseModel):
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    category: str = Field(..., description="Product category")
    brand: str = Field(..., description="Product brand")
    attributes: List[ProductAttribute] = Field(default=[], description="Product attributes like size, color, etc.")
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity")
    images: List[str] = Field(default=[], description="List of image URLs")

class ProductResponse(BaseModel):
    id: str = Field(..., alias="_id")
    name: str
    description: str
    price: float
    category: str
    brand: str
    attributes: List[ProductAttribute]
    stock_quantity: int
    images: List[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True

class ProductsListResponse(BaseModel):
    products: List[ProductResponse]
    total_count: int
    limit: int
    offset: int

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity ordered")
    price_per_item: float = Field(..., gt=0, description="Price per item at the time of order")

class CreateOrderRequest(BaseModel):
    user_id: str = Field(..., description="User ID placing the order")
    items: List[OrderItem] = Field(..., min_items=1, description="List of items in the order")
    shipping_address: Dict[str, Any] = Field(..., description="Shipping address details")
    payment_method: str = Field(..., description="Payment method used")

class OrderItemResponse(BaseModel):
    product_id: str
    quantity: int
    price_per_item: float
    total_price: float

class OrderResponse(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    items: List[OrderItemResponse]
    total_amount: float
    shipping_address: Dict[str, Any]
    payment_method: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        allow_population_by_field_name = True

class OrdersListResponse(BaseModel):
    orders: List[OrderResponse]
    total_count: int
    limit: int
    offset: int

# Helper function to convert ObjectId to string
def serialize_doc(doc):
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

# API Endpoints

@app.post("/products", status_code=201, response_model=ProductResponse)
async def create_product(product: CreateProductRequest):
    """
    Create a new product
    """
    try:
        # Convert attributes to dictionary format for MongoDB
        attributes_dict = {attr.name: attr.value for attr in product.attributes}
        
        product_doc = {
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "category": product.category,
            "brand": product.brand,
            "attributes": attributes_dict,
            "stock_quantity": product.stock_quantity,
            "images": product.images,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await database.products.insert_one(product_doc)
        
        # Fetch the created product
        created_product = await database.products.find_one({"_id": result.inserted_id})
        
        # Convert attributes back to list format for response
        if created_product:
            created_product["attributes"] = [
                ProductAttribute(name=k, value=v) 
                for k, v in created_product["attributes"].items()
            ]
            
        return ProductResponse(**serialize_doc(created_product))
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@app.get("/products", status_code=200, response_model=ProductsListResponse)
async def list_products(
    name: Optional[str] = Query(None, description="Filter by product name (supports partial matching)"),
    size: Optional[str] = Query(None, description="Filter by size attribute"),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip")
):
    """
    List products with optional filtering and pagination
    """
    try:
        # Build filter query
        filter_query = {}
        
        if name:
            # Use regex for partial name matching (case-insensitive)
            filter_query["name"] = {"$regex": re.escape(name), "$options": "i"}
        
        if size:
            filter_query["attributes.size"] = size
        
        # Get total count for pagination info
        total_count = await database.products.count_documents(filter_query)
        
        # Fetch products with pagination
        cursor = database.products.find(filter_query).skip(offset).limit(limit)
        products = await cursor.to_list(length=limit)
        
        # Convert attributes back to list format for response
        product_responses = []
        for product in products:
            product["attributes"] = [
                ProductAttribute(name=k, value=v) 
                for k, v in product["attributes"].items()
            ]
            product_responses.append(ProductResponse(**serialize_doc(product)))
        
        return ProductsListResponse(
            products=product_responses,
            total_count=total_count,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

@app.post("/orders", status_code=201, response_model=OrderResponse)
async def create_order(order: CreateOrderRequest):
    """
    Create a new order
    """
    try:
        # Validate products exist and calculate total
        total_amount = 0.0
        order_items = []
        
        for item in order.items:
            # Verify product exists
            product = await database.products.find_one({"_id": ObjectId(item.product_id)})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            # Check stock availability
            if product["stock_quantity"] < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for product {item.product_id}. Available: {product['stock_quantity']}, Requested: {item.quantity}"
                )
            
            item_total = item.price_per_item * item.quantity
            total_amount += item_total
            
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity,
                "price_per_item": item.price_per_item,
                "total_price": item_total
            })
        
        # Create order document
        order_doc = {
            "user_id": order.user_id,
            "items": order_items,
            "total_amount": total_amount,
            "shipping_address": order.shipping_address,
            "payment_method": order.payment_method,
            "status": "pending",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await database.orders.insert_one(order_doc)
        
        # Update stock quantities
        for item in order.items:
            await database.products.update_one(
                {"_id": ObjectId(item.product_id)},
                {"$inc": {"stock_quantity": -item.quantity}}
            )
        
        # Fetch the created order
        created_order = await database.orders.find_one({"_id": result.inserted_id})
        
        return OrderResponse(**serialize_doc(created_order))
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@app.get("/orders/{user_id}", status_code=200, response_model=OrdersListResponse)
async def get_user_orders(
    user_id: str,
    limit: int = Query(10, ge=1, le=100, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip")
):
    """
    Get list of orders for a specific user
    """
    try:
        filter_query = {"user_id": user_id}
        
        # Get total count for pagination info
        total_count = await database.orders.count_documents(filter_query)
        
        # Fetch orders with pagination (sorted by created_at descending)
        cursor = database.orders.find(filter_query).sort("created_at", -1).skip(offset).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        order_responses = [OrderResponse(**serialize_doc(order)) for order in orders]
        
        return OrdersListResponse(
            orders=order_responses,
            total_count=total_count,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

# Health check endpoint
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)