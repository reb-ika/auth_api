from sqlalchemy.orm import Session
from . import models, schemas, auth
from fastapi import HTTPException
import random
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def create_user(db: Session, user: schemas.UserCreate):
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        name=user.name,
        email=user.email,
        hashed_password=hashed_password,
        is_verified=False
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    logger.info(f"New user registered: {user.email}")
    return db_user

def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return None
    return user

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
        logger.info(f"User deleted: ID {user_id}")
        return True
    return False

def mark_user_verified(db: Session, email: str):
    user = get_user_by_email(db, email)
    if user:
        user.is_verified = True
        db.commit()
        logger.info(f"User verified: {email}")
        return True
    return False

def create_verification_code(db: Session, email: str):
    db.query(models.VerificationCode).filter(models.VerificationCode.email == email).delete()
    code = f"{random.randint(100000, 999999)}"
    expires_at = datetime.utcnow() + timedelta(minutes=10)
    ver_code = models.VerificationCode(email=email, code=code, expires_at=expires_at)
    db.add(ver_code)
    db.commit()
    db.refresh(ver_code)
    return code

def verify_code(db: Session, email: str, code: str):
    ver = db.query(models.VerificationCode).filter(
        models.VerificationCode.email == email,
        models.VerificationCode.code == code
    ).first()
    if not ver or ver.expires_at < datetime.utcnow():
        return False
    db.delete(ver)
    db.commit()
    return True