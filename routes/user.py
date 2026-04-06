from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, RefreshToken
from schemas import UserResponse, MessageResponse
from auth import get_current_user

router = APIRouter(prefix="/user", tags=["User Management"])

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at
    )

@router.delete("/delete-account", response_model=MessageResponse)
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Delete refresh tokens first
    db.query(RefreshToken).filter(RefreshToken.user_id == current_user.id).delete()
    
    # Delete user
    db.delete(current_user)
    db.commit()
    
    return MessageResponse(
        message="Account deleted successfully",
        success=True
    )