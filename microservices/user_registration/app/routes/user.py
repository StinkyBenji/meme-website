from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, crud
from ..db import get_db

router = APIRouter()

@router.post("/register", response_model=schemas.UserResponse)
async def register_user(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if user already exists
    existing_user = await crud.get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_user = await crud.get_user_by_username(db, user.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Create a new user
    return await crud.create_user(db, user)
