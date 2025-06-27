from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongodb = MongoDB()

async def connect_to_mongo():
    """Create database connection"""
    mongodb.client = AsyncIOMotorClient(os.getenv("MONGODB_URL", "mongodb://localhost:27017"))
    mongodb.database = mongodb.client.shopsavvy
    print("Connected to MongoDB!")

async def close_mongo_connection():
    """Close database connection"""
    mongodb.client.close()
    print("Disconnected from MongoDB!")

def get_database():
    return mongodb.database
