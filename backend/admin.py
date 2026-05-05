"""
admin.py — Admin-only API routes for managing users and platform stats.
All endpoints require a valid JWT token from an `is_admin=True` account.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from database import get_db
import models
from auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# ── Helpers ───────────────────────────────────────────────────────────────────

def require_admin(current_user: models.User = Depends(get_current_user)):
    """Dependency: raises 403 if the caller is not an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required."
        )
    return current_user


def _user_to_dict(u: models.User, db: Session) -> dict:
    p = db.query(models.Profile).filter(models.Profile.user_id == u.id).first()
    return {
        "id": u.id,
        "email": u.email,
        "is_active": u.is_active,
        "is_admin": u.is_admin,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "full_name": p.full_name if p else None,
        "affiliation": p.affiliation if p else None,
        "phone_number": p.phone_number if p else None,
        "notification_preferences": p.notification_preferences if p else None,
    }


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserRoleUpdate(BaseModel):
    is_admin: bool

class UserStatusUpdate(BaseModel):
    is_active: bool

class AdminProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    affiliation: Optional[str] = None
    phone_number: Optional[str] = None
    is_admin: Optional[bool] = None
    is_active: Optional[bool] = None


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/stats")
def get_platform_stats(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Returns high-level platform statistics for the admin dashboard."""
    total_users    = db.query(models.User).count()
    active_users   = db.query(models.User).filter(models.User.is_active == True).count()
    pending_users  = db.query(models.User).filter(models.User.is_active == False).count()
    admin_count    = db.query(models.User).filter(models.User.is_admin == True).count()

    return {
        "total_users": total_users,
        "active_users": active_users,
        "pending_verification": pending_users,
        "admin_count": admin_count,
    }


@router.get("/users")
def list_all_users(
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Returns the full user list with profile details."""
    users = db.query(models.User).order_by(models.User.created_at.desc()).all()
    return {"users": [_user_to_dict(u, db) for u in users]}


@router.get("/users/{user_id}")
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Returns a single user's full details."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_dict(u, db)


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Promote or demote a user to/from admin."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own admin role.")
    u.is_admin = payload.is_admin
    db.commit()
    action = "Promoted to admin" if payload.is_admin else "Revoked admin role"
    return {"message": f"{action} for {u.email}"}


@router.patch("/users/{user_id}/status")
def update_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Activate or deactivate (suspend) a user account."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot modify your own status.")
    u.is_active = payload.is_active
    db.commit()
    action = "Activated" if payload.is_active else "Suspended"
    return {"message": f"{action} account for {u.email}"}


@router.patch("/users/{user_id}/profile")
def admin_edit_user_profile(
    user_id: int,
    payload: AdminProfileUpdate,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Admin can edit any user's profile fields and role/status in one call."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user flags
    if payload.is_admin is not None and u.id != admin.id:
        u.is_admin = payload.is_admin
    if payload.is_active is not None and u.id != admin.id:
        u.is_active = payload.is_active

    # Update profile
    p = db.query(models.Profile).filter(models.Profile.user_id == user_id).first()
    if not p:
        p = models.Profile(user_id=user_id)
        db.add(p)

    if payload.full_name is not None:
        p.full_name = payload.full_name
    if payload.affiliation is not None:
        p.affiliation = payload.affiliation
    if payload.phone_number is not None:
        p.phone_number = payload.phone_number

    db.commit()
    return {"message": "User updated successfully", "user": _user_to_dict(u, db)}


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin)
):
    """Permanently deletes a user and all associated records."""
    u = db.query(models.User).filter(models.User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if u.id == admin.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account via admin panel.")
    email = u.email
    db.delete(u)
    db.commit()
    return {"message": f"User {email} permanently deleted."}
