# models.py
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from bson import ObjectId

class CreateProductRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: float = Field(..., gt=0)
    size: str = Field(..., min_length=1, max_length=50)
    description: Optional[str] = None

class OrderItem(BaseModel):
    product_id: str
    quantity: int = Field(..., gt=0, le=100)
    
    @validator('product_id')
    def validate_product_id(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid product ID')
        return v

class CreateOrderRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    items: List[OrderItem] = Field(..., min_items=1, max_items=50)