from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Import the in-memory users from auth_working
from app.routers.auth_working import users_db

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token - In-memory version"""
    try:
        # Verify JWT token
        token_data = auth_service.verify_token(credentials.credentials)
        user_id = token_data["user_id"]  # This should work now
        
        logger.info(f"Token data: {token_data}")
        logger.info(f"Looking for user_id: {user_id}")
        logger.info(f"Users in storage: {[user['id'] for user in users_db.values()]}")
        
        # Find user in in-memory storage by user_id
        for email, user_data in users_db.items():
            if user_data["id"] == user_id:
                logger.info(f"Found user: {user_data['email']}")
                return user_data
        
        # User not found
        logger.warning(f"User with id {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
