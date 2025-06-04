from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

from app.core.config import settings
from app.repositories import repositories
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# Pydantic models
class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    subscription_tier: Optional[str] = "free"

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: str
    subscription_tier: str
    is_active: bool
    created_at: datetime
    favorite_stations: List[str] = []

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[str] = None
    subscription_tier: Optional[str] = None

class FavoriteStationUpdate(BaseModel):
    station_id: str
    action: str  # 'add' or 'remove'

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_user_by_email(email: str):
    """Get user by email from database"""
    try:
        user = await repositories.users.find_by_email(email)
        return user
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

async def authenticate_user(email: str, password: str):
    """Authenticate user with email and password"""
    try:
        user = await repositories.users.authenticate_user(email, password)
        return user
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        subscription_tier: str = payload.get("subscription_tier")
        if email is None or user_id is None:
            raise credentials_exception
        token_data = TokenData(email=email, user_id=user_id, subscription_tier=subscription_tier)
    except JWTError:
        raise credentials_exception
    
    # Use user_id for lookup instead of email for better uniqueness
    user = await repositories.users.get_by_id(token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

# Routes
@router.post("/register", response_model=UserResponse)
async def register_user(user_in: UserCreateRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = await get_user_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user in database
        created_user = await repositories.users.create_user(
            email=user_in.email,
            password=user_in.password,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone=user_in.phone or "+1234567890",
            subscription_tier=user_in.subscription_tier or "free"
        )
        
        # Return user response
        return UserResponse(
            id=str(created_user.id),
            email=created_user.email,
            first_name=created_user.first_name,
            last_name=created_user.last_name,
            phone=created_user.phone,
            subscription_tier=created_user.subscription_tier,
            is_active=created_user.is_active,
            created_at=created_user.created_at,
            favorite_stations=created_user.favorite_stations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        # Check if it's a duplicate key error
        if "E11000" in str(e) and "email" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during user registration"
        )

@router.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login user and return access token with user info"""
    try:
        user = await authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Update last login
        await repositories.users.update_last_login(user.id)
        
        # Create access token with email, user_id, and subscription_tier
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={
                "sub": user.email,
                "user_id": str(user.id),
                "subscription_tier": user.subscription_tier
            }, 
            expires_delta=access_token_expires
        )
        
        # Return token with user info
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "user": UserResponse(
                id=str(user.id),
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=user.phone,
                subscription_tier=user.subscription_tier,
                is_active=user.is_active,
                created_at=user.created_at,
                favorite_stations=user.favorite_stations
            )
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user's information"""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        phone=current_user.phone,
        subscription_tier=current_user.subscription_tier,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        favorite_stations=current_user.favorite_stations
    )

@router.post("/logout")
async def logout():
    """Logout user - client should handle token removal"""
    return {"message": "Successfully logged out"}

@router.post("/favorites", response_model=UserResponse)
async def update_favorite_station(
    update: FavoriteStationUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Add or remove a station from user's favorites"""
    try:
        user_id = str(current_user.id)
        station_id = update.station_id
        action = update.action

        if action not in ['add', 'remove']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'add' or 'remove'"
            )

        updated_user = await repositories.users.update_favorite_station(user_id, station_id, action)
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return UserResponse(
            id=str(updated_user.id),
            email=updated_user.email,
            first_name=updated_user.first_name,
            last_name=updated_user.last_name,
            phone=updated_user.phone,
            subscription_tier=updated_user.subscription_tier,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            favorite_stations=updated_user.favorite_stations
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating favorite station: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while updating favorite station"
        ) 