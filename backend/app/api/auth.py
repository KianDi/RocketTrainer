"""
Authentication endpoints for Steam/Epic OAuth and JWT token management.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import structlog

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserCreate
from app.services.auth_service import AuthService

router = APIRouter()
security = HTTPBearer()
logger = structlog.get_logger()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            credentials.credentials, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user


@router.post("/steam-login", response_model=Token)
async def steam_login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with Steam OpenID.
    This is a simplified version - in production, implement full Steam OpenID flow.
    """
    try:
        # Verify Steam token (simplified for MVP)
        steam_id = user_login.steam_id
        if not steam_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Steam ID is required"
            )
        
        # Find or create user
        user = db.query(User).filter(User.steam_id == steam_id).first()
        if not user:
            # Create new user
            user = User(
                steam_id=steam_id,
                username=user_login.username or f"Player_{steam_id[-6:]}",
                platform="steam",
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info("New user created", user_id=str(user.id), steam_id=steam_id)
        
        # Create access token
        access_token = AuthService.create_access_token(
            data={"sub": str(user.id), "username": user.username}
        )
        
        logger.info("User authenticated", user_id=str(user.id), steam_id=steam_id)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "steam_id": user.steam_id,
                "current_rank": user.current_rank
            }
        }
        
    except Exception as e:
        logger.error("Steam login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/register", response_model=Token)
async def register_user(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if user already exists
    existing_user = None
    if user_create.steam_id:
        existing_user = db.query(User).filter(User.steam_id == user_create.steam_id).first()
    elif user_create.epic_id:
        existing_user = db.query(User).filter(User.epic_id == user_create.epic_id).first()
    elif user_create.email:
        existing_user = db.query(User).filter(User.email == user_create.email).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists"
        )
    
    # Create new user
    user = User(
        steam_id=user_create.steam_id,
        epic_id=user_create.epic_id,
        username=user_create.username,
        email=user_create.email,
        platform=user_create.platform,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access token
    access_token = AuthService.create_access_token(
        data={"sub": str(user.id), "username": user.username}
    )
    
    logger.info("New user registered", user_id=str(user.id), username=user.username)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": {
            "id": str(user.id),
            "username": user.username,
            "steam_id": user.steam_id,
            "epic_id": user.epic_id,
            "current_rank": user.current_rank
        }
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should discard token)."""
    logger.info("User logged out", user_id=str(current_user.id))
    return {"message": "Successfully logged out"}


@router.get("/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "steam_id": current_user.steam_id,
        "epic_id": current_user.epic_id,
        "email": current_user.email,
        "current_rank": current_user.current_rank,
        "platform": current_user.platform,
        "is_premium": current_user.is_premium,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login
    }
