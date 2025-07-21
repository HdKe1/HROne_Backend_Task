# main.py
from fastapi import FastAPI, HTTPException, Query, Depends
from typing import Optional
from datetime import datetime
from bson import ObjectId
from .models import CreateOrderRequest,CreateProductRequest
from .database import get_database, serialize_doc

app = FastAPI(title="E-commerce API", version="1.0.0")

# Routes
@app.get("/")
async def root():
    return {"message": "E-commerce API", "status": "running"}

@app.get("/health")
async def health():
    try:
        db = await get_database()
        await db.command('ping')
        return {"status": "healthy", "database": "connected"}
    except Exception:
        return {"status": "healthy", "database": "disconnected"}

@app.post("/products", status_code=201)
async def create_product(product: CreateProductRequest, db=Depends(get_database)):
    try:
        product_doc = {
            "name": product.name,
            "price": product.price,
            "size": product.size,
            "description": product.description,
            "created_at": datetime.utcnow()
        }
        
        result = await db.products.insert_one(product_doc)
        created_product = await db.products.find_one({"_id": result.inserted_id})
        
        return serialize_doc(created_product)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products")
async def list_products(
    name: Optional[str] = Query(None),
    size: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_database)
):
    try:
        filter_query = {}
        
        if name:
            filter_query["name"] = {"$regex": name, "$options": "i"}
        if size:
            filter_query["size"] = size
        
        total_count = await db.products.count_documents(filter_query)
        
        cursor = db.products.find(filter_query).skip(offset).limit(limit)
        products = await cursor.to_list(length=limit)
        
        return {
            "products": [serialize_doc(p) for p in products],
            "total": total_count,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/orders", status_code=201)
async def create_order(order: CreateOrderRequest, db=Depends(get_database)):
    try:
        total_amount = 0.0
        order_items = []
        
        for item in order.items:
            product = await db.products.find_one({"_id": ObjectId(item.product_id)})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")
            
            item_total = product["price"] * item.quantity
            total_amount += item_total
            
            order_items.append({
                "product_id": item.product_id,
                "quantity": item.quantity
            })
        
        order_doc = {
            "user_id": order.user_id,
            "items": order_items,
            "total_amount": total_amount,
            "created_at": datetime.utcnow()
        }
        
        result = await db.orders.insert_one(order_doc)
        created_order = await db.orders.find_one({"_id": result.inserted_id})
        
        return serialize_doc(created_order)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/orders/{user_id}")
async def get_user_orders(
    user_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db=Depends(get_database)
):
    try:
        filter_query = {"user_id": user_id}
        
        total_count = await db.orders.count_documents(filter_query)
        
        cursor = db.orders.find(filter_query).skip(offset).limit(limit)
        orders = await cursor.to_list(length=limit)
        
        return {
            "orders": [serialize_doc(o) for o in orders],
            "total": total_count,
            "limit": limit,
            "offset": offset,
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)