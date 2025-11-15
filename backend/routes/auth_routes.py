"""
Authentication routes
POST /api/auth/signup, /api/auth/login, /api/auth/logout
GET /api/auth/me
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from database import get_db
import crud
from auth import create_access_token, get_current_user, get_optional_user
import models

router = APIRouter()


# Request/Response models
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    display_name: Optional[str]

    class Config:
        from_attributes = True


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest, response: Response, db: Session = Depends(get_db)):
    """
    Create a new user account
    """
    # Check if user already exists
    existing_user = crud.get_user_by_email(db, email=request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Create user
    user = crud.create_user(
        db=db,
        email=request.email,
        password=request.password,
        display_name=request.display_name
    )

    # Create session token
    access_token = create_access_token(data={"sub": user.id})

    # Set HTTP-only cookie
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7  # 7 days
    )

    return user


@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    """
    Login with email and password
    """
    # Get user
    user = crud.get_user_by_email(db, email=request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Verify password
    if not crud.verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    # Create session token
    access_token = create_access_token(data={"sub": user.id})

    # Set HTTP-only cookie
    response.set_cookie(
        key="session_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * 7  # 7 days
    )

    return user


@router.post("/logout")
async def logout(response: Response):
    """
    Logout - clear session cookie
    """
    response.delete_cookie(key="session_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: models.User = Depends(get_current_user)):
    """
    Get current authenticated user info
    """
    return current_user
