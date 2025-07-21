# database.py
import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "ecommerce_db")

# Database connection
client = AsyncIOMotorClient(MONGODB_URL)
database = client[DATABASE_NAME]

def serialize_doc(doc):
    """Convert ObjectId to string for JSON serialization"""
    if doc is None:
        return None
    doc["_id"] = str(doc["_id"])
    return doc

async def get_database():
    """Dependency to get database instance"""
    return database