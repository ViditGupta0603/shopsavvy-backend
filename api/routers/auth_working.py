from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from api.services.auth_service import auth_service
from bson import ObjectId
from datetime import timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# File-based persistence for users
USERS_FILE = "users_data.json"

def load_users():
    """Load users from file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading users: {e}")
    return {}

def save_users():
    """Save users to file"""
    try:
        with open(USERS_FILE, 'w') as f:
            json.dump(users_db, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving users: {e}")

# Load users on startup
users_db = load_users()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

@router.post("/register")
async def register(user_data: UserCreate):
    """Register a new user"""
    try:
        # Check if user exists
        if user_data.email in users_db:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Generate MongoDB-compatible ObjectId
        user_id = str(ObjectId())
        
        # Hash password and store user
        hashed_password = auth_service.get_password_hash(user_data.password)
        
        users_db[user_data.email] = {
            "id": user_id,
            "email": user_data.email,
            "password": hashed_password,
            "full_name": user_data.full_name,
            "is_active": True
        }
        
        # Save to file
        save_users()
        
        return {
            "id": user_id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "is_active": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login")
async def login(user_data: UserLogin):
    """Login user and return JWT token"""
    try:
        # Check if user exists
        if user_data.email not in users_db:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        stored_user = users_db[user_data.email]
        
        # Verify password
        if not auth_service.verify_password(user_data.password, stored_user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create JWT token
        access_token = auth_service.create_access_token(
            data={"sub": stored_user["id"], "email": stored_user["email"]}
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": stored_user["id"],
                "email": stored_user["email"],
                "full_name": stored_user["full_name"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/test")
async def test_auth():
    """Test endpoint"""
    return {
        "message": "Auth is working!",
        "users_count": len(users_db)
    }
