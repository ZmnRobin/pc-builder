"""
Script to clear database for fresh testing
"""
from pymongo import MongoClient

def clear_database():
    """Clear all components from database"""
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['pcbuilder_db']
        components = db['components']
        
        # Count before clearing
        count_before = components.count_documents({})
        print(f"Components in database before clearing: {count_before}")
        
        # Clear all components
        result = components.delete_many({})
        print(f"Deleted {result.deleted_count} components")
        
        # Count after clearing
        count_after = components.count_documents({})
        print(f"Components in database after clearing: {count_after}")
        
        client.close()
        print("✅ Database cleared successfully!")
        
    except Exception as e:
        print(f"❌ Error clearing database: {e}")

if __name__ == "__main__":
    print("🗑️ Clearing PC Builder Database")
    print("=" * 40)
    clear_database()
