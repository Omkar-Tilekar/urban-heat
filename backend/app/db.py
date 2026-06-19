import os
import pymongo
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGODB_DB_NAME", "urban_heat")

_client = None

def get_mongo_client():
    global _client
    if _client is not None:
        return _client
        
    if not MONGODB_URI:
        print("MongoDB URI not configured in environment. Falling back to local file storage.")
        return None
        
    try:
        # Create MongoDB client with a short selection timeout (3 seconds) to ensure quick fallback
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
        # Ping the admin database to verify the connection is active
        client.admin.command('ping')
        _client = client
        print(f"Successfully connected to MongoDB database: {DB_NAME}")
        return _client
    except (ConnectionFailure, Exception) as e:
        print(f"MongoDB connection check failed: {e}. Gracefully falling back to local file storage.")
        return None

def get_db():
    client = get_mongo_client()
    if client is not None:
        return client[DB_NAME]
    return None
