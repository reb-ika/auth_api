from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import random
from database import get_db
from models import User, VerificationCode
from schemas import VerificationCodeRequest, VerificationRequest, MessageResponse
from auth import get_current_user
from utils.email_simulator import simulate_send_email

router = APIRouter(prefix="/verification", tags=["Email Verification"])

def generate_verification_code():
    return f"{random.randint(100000, 999999)}"

def cleanup_expired_codes(db: Session):
    """Clean up expired verification codes"""
    db.query(VerificationCode).filter(
        VerificationCode.expires_at < datetime.now(timezone.utc)
    ).delete()
    db.commit()

@router.post("/send-code", response_model=MessageResponse)
def send_verification_code(
    request: VerificationCodeRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    # Check if user exists
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Clean up expired codes
    cleanup_expired_codes(db)
    
    # Generate new code
    code = generate_verification_code()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)
    
    # Store or update code
    existing_code = db.query(VerificationCode).filter(
        VerificationCode.email == request.email
    ).first()
    
    if existing_code:
        existing_code.code = code
        existing_code.expires_at = expires_at
        existing_code.created_at = datetime.now(timezone.utc)
    else:
        new_code = VerificationCode(
            email=request.email,
            code=code,
            expires_at=expires_at
        )
        db.add(new_code)
    
    db.commit()
    
    # Simulate sending email
    background_tasks.add_task(simulate_send_email, request.email, code)
    
    return MessageResponse(
        message=f"Verification code sent to {request.email}",
        success=True
    )

@router.post("/verify", response_model=MessageResponse)
def verify_email(
    request: VerificationRequest,
    db: Session = Depends(get_db)
):
    # Find verification code
    verification = db.query(VerificationCode).filter(
        VerificationCode.email == request.email,
        VerificationCode.code == request.code
    ).first()
    
    if not verification:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    # Check if expired
    if verification.expires_at < datetime.now(timezone.utc):
        db.delete(verification)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired"
        )
    
    # Update user as verified
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_verified = True
    
    # Delete used verification code
    db.delete(verification)
    db.commit()
    
    return MessageResponse(
        message="Email verified successfully",
        success=True
    )