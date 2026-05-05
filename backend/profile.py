from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from database import get_db
import models
from auth import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Profile"])

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    affiliation: Optional[str] = None
    phone_number: Optional[str] = None
    notification_preferences: Optional[str] = None

@router.get("/")
def get_my_profile(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
    if not profile:
        # Create empty profile if not exists (fail-safe)
        profile = models.Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
    return {
        "user_email": current_user.email,
        "is_admin": current_user.is_admin,
        "full_name": profile.full_name,
        "affiliation": profile.affiliation,
        "phone_number": profile.phone_number,
        "notification_preferences": profile.notification_preferences
    }

@router.put("/")
def update_profile(updates: ProfileUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    profile = db.query(models.Profile).filter(models.Profile.user_id == current_user.id).first()
    if not profile:
        profile = models.Profile(user_id=current_user.id)
        db.add(profile)

    if updates.full_name is not None:
        profile.full_name = updates.full_name
    if updates.affiliation is not None:
        profile.affiliation = updates.affiliation
    if updates.phone_number is not None:
        profile.phone_number = updates.phone_number
    if updates.notification_preferences is not None:
        profile.notification_preferences = updates.notification_preferences

    db.commit()
    return {"message": "Profile updated successfully"}

# Admin route
@router.get("/all_users")
def get_all_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Insufficient privileges. Admin access required.")
    
    users = db.query(models.User).all()
    user_data = []
    for u in users:
        p = db.query(models.Profile).filter(models.Profile.user_id == u.id).first()
        user_data.append({
            "id": u.id,
            "email": u.email,
            "is_active": u.is_active,
            "is_admin": u.is_admin,
            "full_name": p.full_name if p else None,
            "created_at": u.created_at
        })
    return {"users": user_data}
