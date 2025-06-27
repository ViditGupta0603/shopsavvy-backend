from fastapi import APIRouter, Depends, HTTPException, status
from api.models.user import UserCreate, UserLogin, Token, UserResponse
from api.services.user_service import user_service
from api.services.auth_service import auth_service
from api.core.dependencies import get_current_user
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    """Register a new user"""
    return await user_service.create_user(user_data)

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """Login user and return JWT token"""
    user = await user_service.authenticate_user(user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token = auth_service.create_access_token(
        data={"sub": user["id"], "email": user["email"]}
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user
