# main.py
from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
import re
import os
import ssl
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# MongoDB connection with SSL support
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ecommerce_db")

# Global variables for database
database = None
client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global database, client
    try:
        logger.info("🚀 Starting up application...")
        
        # Create MongoDB client with more robust connection settings
        client = AsyncIOMotorClient(
            MONGODB_URL,
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl_match_hostname=False,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,
            maxPoolSize=10,
            retryWrites=True
        )
        database = client[DATABASE_NAME]
        
        # Test connection with timeout
        try:
            await client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")
        except Exception as db_error:
            logger.warning(f"⚠️  MongoDB connection failed, but continuing: {db_error}")
            # Don't raise here - allow the app to start even without MongoDB
            # This prevents 404 errors on basic endpoints
        
        # Create indexes for better performance (only if database is connected)
        if database:
            try:
                await database.products.create_index("name")
                await database.products.create_index("category")
                await database.products.create_index("brand")
                await database.products.create_index("attributes.size")
                await database.orders.create_index("user_id")
                await database.orders.create_index("created_at")
                await database.orders.create_index([("user_id", 1), ("created_at", -1)])
                logger.info("✅ Database indexes created successfully")
            except Exception as index_error:
                logger.warning(f"⚠️  Failed to create indexes: {index_error}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        # Don't raise the exception - let the app start anyway
        # This prevents 404 errors on basic endpoints
    
    yield
    
    # Shutdown
    try:
        if client:
            client.close()
            logger.info("🔌 MongoDB connection closed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

# Create FastAPI app
app = FastAPI(
    title="Ecommerce API",
    description="A FastAPI-based ecommerce application similar to Flipkart/Amazon",
    version="1.0.0",
    lifespan=lifespan
)

# Pydantic models for request/response validation

class ProductAttribute(BaseModel):
    name: str = Field(..., min_length=1, description="Attribute name")
    value: str = Field(..., min_length=1, description="Attribute value")

class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    description: str = Field(..., min_length=10, max_length=2000, description="Product description")
    price: float = Field(..., gt=0, description="Product price (must be positive)")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")
    brand: str = Field(..., min_length=1, max_length=100, description="Product brand")
    attributes: List[ProductAttribute] = Field(default=[], description="Product attributes like size, color, etc.")
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity")
    images: List[str] = Field(default=[], description="List of image URLs")
    
    @validator('images')
    def validate_images(cls, v):
        if len(v) > 10:  # Limit to 10 images
            raise ValueError('Maximum 10 images allowed')
        return v

class UpdateProductRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    attributes: Optional[List[ProductAttribute]] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    images: Optional[List[str]] = None

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
    has_more: bool

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, le=100, description="Quantity ordered (max 100)")
    price_per_item: Optional[float] = Field(None, gt=0, description="Price per item (auto-filled if not provided)")
    
    @validator('product_id')
    def validate_product_id(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid product ID format')
        return v

class CreateOrderRequest(BaseModel):
    user_id: str = Field(..., min_length=1, description="User ID placing the order")
    items: List[OrderItem] = Field(..., min_items=1, max_items=50, description="List of items in the order")
    shipping_address: Dict[str, Any] = Field(..., description="Shipping address details")
    payment_method: str = Field(..., description="Payment method used")
    
    @validator('shipping_address')
    def validate_shipping_address(cls, v):
        required_fields = ['street', 'city', 'state', 'zip_code', 'country']
        for field in required_fields:
            if field not in v:
                raise ValueError(f'Missing required field in shipping address: {field}')
        return v
    
    @validator('payment_method')
    def validate_payment_method(cls, v):
        valid_methods = ['credit_card', 'debit_card', 'paypal', 'upi', 'cod']
        if v.lower() not in valid_methods:
            raise ValueError(f'Invalid payment method. Must be one of: {valid_methods}')
        return v.lower()

class OrderItemResponse(BaseModel):
    product_id: str
    product_name: str
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
    has_more: bool

class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., description="New order status")
    
    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded']
        if v.lower() not in valid_statuses:
            raise ValueError(f'Invalid status. Must be one of: {valid_statuses}')
        return v.lower()

# Helper functions
def serialize_doc(doc):
    """Convert ObjectId to string for JSON serialization"""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def get_database():
    """Dependency to get database instance"""
    if database is None:
        raise HTTPException(status_code=503, detail="Database connection not available. Please check your MongoDB connection.")
    return database

async def product_exists(product_id: str, db) -> dict:
    """Check if product exists and return it"""
    if not ObjectId.is_valid(product_id):
        raise HTTPException(status_code=400, detail="Invalid product ID format")
    
    product = await db.products.find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
    
    return product

# API Endpoints

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - Always accessible"""
    return {
        "message": "Welcome to Ecommerce API", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint - Always accessible"""
    try:
        # Test database connection
        if database:
            await database.command('ping')
            db_status = "connected"
        else:
            db_status = "disconnected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/products", status_code=201, response_model=ProductResponse, tags=["Products"])
async def create_product(product: CreateProductRequest, db=Depends(get_database)):
    """Create a new product"""
    try:
        # Check if product with same name already exists
        existing_product = await db.products.find_one({"name": {"$regex": f"^{re.escape(product.name)}$", "$options": "i"}})
        if existing_product:
            raise HTTPException(status_code=400, detail="Product with this name already exists")
        
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
        
        result = await db.products.insert_one(product_doc)
        
        # Fetch the created product
        created_product = await db.products.find_one({"_id": result.inserted_id})
        
        # Convert attributes back to list format for response
        if created_product:
            created_product["attributes"] = [
                ProductAttribute(name=k, value=v) 
                for k, v in created_product["attributes"].items()
            ]
            
        logger.info(f"Product created: {created_product['name']} (ID: {result.inserted_id})")
        return ProductResponse(**serialize_doc(created_product))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create product: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")

@app.get("/products", status_code=200, response_model=ProductsListResponse, tags=["Products"])
async def list_products(
    name: Optional[str] = Query(None, description="Filter by product name (supports partial matching)"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    size: Optional[str] = Query(None, description="Filter by size attribute"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter products in stock"),
    limit: int = Query(10, ge=1, le=100, description="Number of products to return"),
    offset: int = Query(0, ge=0, description="Number of products to skip"),
    db=Depends(get_database)
):
    """List products with optional filtering and pagination"""
    try:
        # Build filter query
        filter_query = {}
        
        if name:
            filter_query["name"] = {"$regex": re.escape(name), "$options": "i"}
        
        if category:
            filter_query["category"] = {"$regex": re.escape(category), "$options": "i"}
            
        if brand:
            filter_query["brand"] = {"$regex": re.escape(brand), "$options": "i"}
        
        if size:
            filter_query["attributes.size"] = size
            
        if min_price is not None or max_price is not None:
            price_filter = {}
            if min_price is not None:
                price_filter["$gte"] = min_price
            if max_price is not None:
                price_filter["$lte"] = max_price
            filter_query["price"] = price_filter
            
        if in_stock is True:
            filter_query["stock_quantity"] = {"$gt": 0}
        elif in_stock is False:
            filter_query["stock_quantity"] = {"$eq": 0}
        
        # Get total count for pagination info
        total_count = await db.products.count_documents(filter_query)
        
        # Fetch products with pagination
        cursor = db.products.find(filter_query).skip(offset).limit(limit).sort("created_at", -1)
        products = await cursor.to_list(length=limit)
        
        # Convert attributes back to list format for response
        product_responses = []
        for product in products:
            product["attributes"] = [
                ProductAttribute(name=k, value=v) 
                for k, v in product.get("attributes", {}).items()
            ]
            product_responses.append(ProductResponse(**serialize_doc(product)))
        
        has_more = offset + limit < total_count
        
        return ProductsListResponse(
            products=product_responses,
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch products: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch products: {str(e)}")

@app.get("/products/{product_id}", status_code=200, response_model=ProductResponse, tags=["Products"])
async def get_product(product_id: str, db=Depends(get_database)):
    """Get a specific product by ID"""
    try:
        product = await product_exists(product_id, db)
        
        # Convert attributes back to list format for response
        product["attributes"] = [
            ProductAttribute(name=k, value=v) 
            for k, v in product.get("attributes", {}).items()
        ]
        
        return ProductResponse(**serialize_doc(product))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch product: {str(e)}")

@app.put("/products/{product_id}", status_code=200, response_model=ProductResponse, tags=["Products"])
async def update_product(product_id: str, product_update: UpdateProductRequest, db=Depends(get_database)):
    """Update a product"""
    try:
        # Check if product exists
        await product_exists(product_id, db)
        
        # Build update document
        update_doc = {"updated_at": datetime.utcnow()}
        
        if product_update.name is not None:
            update_doc["name"] = product_update.name
        if product_update.description is not None:
            update_doc["description"] = product_update.description
        if product_update.price is not None:
            update_doc["price"] = product_update.price
        if product_update.category is not None:
            update_doc["category"] = product_update.category
        if product_update.brand is not None:
            update_doc["brand"] = product_update.brand
        if product_update.stock_quantity is not None:
            update_doc["stock_quantity"] = product_update.stock_quantity
        if product_update.images is not None:
            update_doc["images"] = product_update.images
        if product_update.attributes is not None:
            update_doc["attributes"] = {attr.name: attr.value for attr in product_update.attributes}
        
        # Update product
        await db.products.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_doc}
        )
        
        # Fetch updated product
        updated_product = await db.products.find_one({"_id": ObjectId(product_id)})
        
        # Convert attributes back to list format for response
        updated_product["attributes"] = [
            ProductAttribute(name=k, value=v) 
            for k, v in updated_product.get("attributes", {}).items()
        ]
        
        logger.info(f"Product updated: {product_id}")
        return ProductResponse(**serialize_doc(updated_product))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")

@app.delete("/products/{product_id}", status_code=204, tags=["Products"])
async def delete_product(product_id: str, db=Depends(get_database)):
    """Delete a product"""
    try:
        # Check if product exists
        await product_exists(product_id, db)
        
        # Delete product
        result = await db.products.delete_one({"_id": ObjectId(product_id)})
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        logger.info(f"Product deleted: {product_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")

@app.post("/orders", status_code=201, response_model=OrderResponse, tags=["Orders"])
async def create_order(order: CreateOrderRequest, db=Depends(get_database)):
    """Create a new order"""
    try:
        # Validate products exist and calculate total
        total_amount = 0.0
        order_items = []
        
        for item in order.items:
            # Verify product exists
            product = await product_exists(item.product_id, db)
            
            # Check stock availability
            if product["stock_quantity"] < item.quantity:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient stock for product {item.product_id}. Available: {product['stock_quantity']}, Requested: {item.quantity}"
                )
            
            # Use product's current price if not provided
            price_per_item = item.price_per_item if item.price_per_item is not None else product["price"]
            item_total = price_per_item * item.quantity
            total_amount += item_total
            
            order_items.append({
                "product_id": item.product_id,
                "product_name": product["name"],
                "quantity": item.quantity,
                "price_per_item": price_per_item,
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
        
        result = await db.orders.insert_one(order_doc)
        
        # Update stock quantities
        for item in order.items:
            await db.products.update_one(
                {"_id": ObjectId(item.product_id)},
                {
                    "$inc": {"stock_quantity": -item.quantity},
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
        
        # Fetch the created order
        created_order = await db.orders.find_one({"_id": result.inserted_id})
        
        logger.info(f"Order created: {result.inserted_id} for user {order.user_id}")
        return OrderResponse(**serialize_doc(created_order))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")

@app.get("/orders/{user_id}", status_code=200, response_model=OrdersListResponse, tags=["Orders"])
async def get_user_orders(
    user_id: str,
    status: Optional[str] = Query(None, description="Filter by order status"),
    limit: int = Query(10, ge=1, le=100, description="Number of orders to return"),
    offset: int = Query(0, ge=0, description="Number of orders to skip"),
    db=Depends(get_database)
):
    """Get list of orders for a specific user"""
    try:
        filter_query = {"user_id": user_id}
        
        if status:
            filter_query["status"] = status.lower()
        
        # Get total count for pagination info
        total_count = await db.orders.count_documents(filter_query)
        
        # Fetch orders with pagination (sorted by created_at descending)
        cursor = db.orders.find(filter_query).sort("created_at", -1).skip(offset).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        order_responses = [OrderResponse(**serialize_doc(order)) for order in orders]
        has_more = offset + limit < total_count
        
        return OrdersListResponse(
            orders=order_responses,
            total_count=total_count,
            limit=limit,
            offset=offset,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Failed to fetch orders for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch orders: {str(e)}")

@app.get("/orders/detail/{order_id}", status_code=200, response_model=OrderResponse, tags=["Orders"])
async def get_order(order_id: str, db=Depends(get_database)):
    """Get a specific order by ID"""
    try:
        if not ObjectId.is_valid(order_id):
            raise HTTPException(status_code=400, detail="Invalid order ID format")
        
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return OrderResponse(**serialize_doc(order))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch order {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch order: {str(e)}")

@app.patch("/orders/{order_id}/status", status_code=200, response_model=OrderResponse, tags=["Orders"])
async def update_order_status(order_id: str, status_update: UpdateOrderStatusRequest, db=Depends(get_database)):
    """Update order status"""
    try:
        if not ObjectId.is_valid(order_id):
            raise HTTPException(status_code=400, detail="Invalid order ID format")
        
        # Check if order exists
        order = await db.orders.find_one({"_id": ObjectId(order_id)})
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Update order status
        await db.orders.update_one(
            {"_id": ObjectId(order_id)},
            {
                "$set": {
                    "status": status_update.status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Fetch updated order
        updated_order = await db.orders.find_one({"_id": ObjectId(order_id)})
        
        logger.info(f"Order status updated: {order_id} -> {status_update.status}")
        return OrderResponse(**serialize_doc(updated_order))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update order status {order_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update order status: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)