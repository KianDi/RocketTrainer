"""
Authentication service for JWT token management and OAuth integration.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import jwt
from passlib.context import CryptContext
import structlog

from app.config import settings

logger = structlog.get_logger()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication operations."""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            return payload
        except jwt.JWTError as e:
            logger.warning("Token verification failed", error=str(e))
            return None
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def verify_steam_token(steam_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Steam OpenID token.
        This is a placeholder - implement full Steam OpenID verification.
        """
        # TODO: Implement Steam OpenID verification
        # For MVP, we'll accept any steam_id format
        if steam_token and len(steam_token) >= 10:
            return {
                "steam_id": steam_token,
                "verified": True
            }
        return None
    
    @staticmethod
    def verify_epic_token(epic_token: str) -> Optional[Dict[str, Any]]:
        """
        Verify Epic Games OAuth token.
        This is a placeholder - implement Epic Games OAuth verification.
        """
        # TODO: Implement Epic Games OAuth verification
        if epic_token and len(epic_token) >= 10:
            return {
                "epic_id": epic_token,
                "verified": True
            }
        return None
