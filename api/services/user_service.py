from api.database.mongodb import get_database
from api.services.auth_service import auth_service
from api.models.user import UserCreate, UserLogin
from bson import ObjectId
from datetime import datetime
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class UserService:
    def __init__(self):
        self.collection = "users"
    
    def get_db(self):
        """Get database connection dynamically"""
        db = get_database()
        if db is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        return db
    
    async def create_user(self, user_data: UserCreate):
        db = self.get_db()  # Get database dynamically
        
        # Check if user exists
        existing_user = await db[self.collection].find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password and create user
        hashed_password = auth_service.get_password_hash(user_data.password)
        user_doc = {
            "email": user_data.email,
            "password": hashed_password,
            "full_name": user_data.full_name,
            "created_at": datetime.utcnow(),
            "is_active": True
        }
        
        result = await db[self.collection].insert_one(user_doc)
        user_doc["_id"] = result.inserted_id
        return self._format_user(user_doc)
    
    async def authenticate_user(self, email: str, password: str):
        db = self.get_db()  # Get database dynamically
        
        user = await db[self.collection].find_one({"email": email})
        if not user or not auth_service.verify_password(password, user["password"]):
            return False
        return self._format_user(user)
    
    async def get_user_by_id(self, user_id: str):
        db = self.get_db()  # Get database dynamically
        
        user = await db[self.collection].find_one({"_id": ObjectId(user_id)})
        if user:
            return self._format_user(user)
        return None
    
    def _format_user(self, user_doc):
        return {
            "id": str(user_doc["_id"]),
            "email": user_doc["email"],
            "full_name": user_doc.get("full_name"),
            "created_at": user_doc["created_at"],
            "is_active": user_doc.get("is_active", True)
        }

user_service = UserService()
