"""
Database configuration and connection management.
Handles MongoDB connection lifecycle and database operations.
"""
import logging
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Global database variables
client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


class DatabaseManager:
    """Manages MongoDB database connection and operations."""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.database: Optional[AsyncIOMotorDatabase] = None
    
    async def connect(self) -> None:
        """Establish connection to MongoDB."""
        try:
            logger.info("🚀 Connecting to MongoDB...")
            
            # Create MongoDB client with robust connection settings
            self.client = AsyncIOMotorClient(
                settings.mongodb_url,
                serverSelectionTimeoutMS=settings.server_selection_timeout_ms,
                connectTimeoutMS=settings.connect_timeout_ms,
                socketTimeoutMS=settings.socket_timeout_ms,
                maxPoolSize=settings.max_pool_size,
                minPoolSize=settings.min_pool_size,
                retryWrites=settings.retry_writes,
                directConnection=settings.direct_connection,
            )
            
            self.database = self.client[settings.database_name]
            
            # Test connection with timeout
            await self.client.admin.command('ping')
            logger.info("✅ Connected to MongoDB successfully")
            
        except Exception as db_error:
            logger.warning(f"⚠️  MongoDB connection failed: {db_error}")
            # Don't raise here - allow the app to start even without MongoDB
            # This prevents 404 errors on basic endpoints
    
    async def disconnect(self) -> None:
        """Close MongoDB connection."""
        try:
            if self.client is not None:
                self.client.close()
                logger.info("🔌 MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error during database disconnect: {e}")
    
    async def create_indexes(self) -> None:
        """Create database indexes for better performance."""
        if self.database is None:
            logger.warning("Database not connected, skipping index creation")
            return
        
        try:
            # Products collection indexes
            await self.database.products.create_index("name")
            await self.database.products.create_index("size")
            await self.database.products.create_index("category")
            await self.database.products.create_index("brand")
            await self.database.products.create_index("created_at")
            
            # Orders collection indexes
            await self.database.orders.create_index("user_id")
            await self.database.orders.create_index("created_at")
            await self.database.orders.create_index("status")
            await self.database.orders.create_index([("user_id", 1), ("created_at", -1)])
            
            logger.info("✅ Database indexes created successfully")
            
        except Exception as index_error:
            logger.warning(f"⚠️  Failed to create indexes: {index_error}")
    
    def get_database(self) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if self.database is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.database
    
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self.database is not None


# Global database manager instance
db_manager = DatabaseManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for database connection."""
    # Startup
    try:
        logger.info("🚀 Starting up application...")
        await db_manager.connect()
        await db_manager.create_indexes()
        
        # Store database manager in app state for dependency injection
        app.state.db_manager = db_manager
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize application: {e}")
        # Don't raise the exception - let the app start anyway
    
    yield
    
    # Shutdown
    await db_manager.disconnect()


async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency to get database instance."""
    if not db_manager.is_connected():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503, 
            detail="Database connection not available. Please check your MongoDB connection."
        )
    return db_manager.get_database()


def get_database_manager() -> DatabaseManager:
    """Get database manager instance."""
    return db_manager