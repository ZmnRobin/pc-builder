"""
Database initialization and management utilities
"""
import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from config import MONGODB_URL, DATABASE_NAME

logger = logging.getLogger(__name__)

def initialize_database():
    """Initialize database with proper indexes and collections"""
    try:
        client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        logger.info("Connected to MongoDB")
        
        db = client[DATABASE_NAME]
        
        # Create collections if they don't exist
        collections = ["components", "price_history", "build_logs", "user_preferences"]
        for collection_name in collections:
            if collection_name not in db.list_collection_names():
                db.create_collection(collection_name)
                logger.info(f"Created collection: {collection_name}")
        
        # Create indexes for components collection
        components = db["components"]
        
        indexes = [
            # Compound index for category and price queries
            [("category", ASCENDING), ("price_BDT", ASCENDING)],
            # Index for name and category lookups
            [("name", ASCENDING), ("category", ASCENDING)],
            # Index for stock status
            [("stock", ASCENDING)],
            # Index for last updated (for cleanup)
            [("last_updated", DESCENDING)],
            # Index for performance score
            [("performance_score", DESCENDING)],
            # Index for retailer
            [("retailer", ASCENDING)],
            # Text index for search
            [("name", "text"), ("category", "text")]
        ]
        
        for index_fields in indexes:
            try:
                if isinstance(index_fields[0], tuple):
                    # Compound index
                    components.create_index(index_fields)
                else:
                    # Single field index
                    components.create_index(index_fields[0])
                logger.info(f"Created index: {index_fields}")
            except Exception as e:
                logger.debug(f"Index creation warning: {e}")
        
        # Create indexes for price_history collection
        price_history = db["price_history"]
        price_history.create_index([("component_id", ASCENDING), ("date", DESCENDING)])
        price_history.create_index([("date", DESCENDING)])
        
        # Create indexes for build_logs collection
        build_logs = db["build_logs"]
        build_logs.create_index([("timestamp", DESCENDING)])
        build_logs.create_index([("purpose", ASCENDING)])
        build_logs.create_index([("budget_range", ASCENDING)])
        
        logger.info("Database initialization complete")
        return client
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def cleanup_old_data(days_old=30):
    """Clean up old data from database"""
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        from datetime import datetime, timedelta
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Remove old components that haven't been updated
        components = db["components"]
        result = components.delete_many({"last_updated": {"$lt": cutoff_date}})
        logger.info(f"Cleaned up {result.deleted_count} old components")
        
        # Remove old price history
        price_history = db["price_history"]
        result = price_history.delete_many({"date": {"$lt": cutoff_date}})
        logger.info(f"Cleaned up {result.deleted_count} old price records")
        
        client.close()
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")

def get_database_stats():
    """Get database statistics"""
    try:
        client = MongoClient(MONGODB_URL)
        db = client[DATABASE_NAME]
        
        stats = {
            "collections": {},
            "total_size": 0
        }
        
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            count = collection.count_documents({})
            stats["collections"][collection_name] = {
                "count": count,
                "indexes": len(collection.list_indexes())
            }
        
        # Get database size
        stats["total_size"] = db.command("dbStats")["dataSize"]
        
        client.close()
        return stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return None

if __name__ == "__main__":
    # Initialize database when run directly
    initialize_database()
