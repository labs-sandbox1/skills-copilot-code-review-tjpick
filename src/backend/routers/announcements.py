"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from datetime import datetime
from pydantic import BaseModel

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementCreate(BaseModel):
    message: str
    start_date: str | None = None
    expiration_date: str


class AnnouncementUpdate(BaseModel):
    message: str | None = None
    start_date: str | None = None
    expiration_date: str | None = None


@router.get("")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (within date range)"""
    now = datetime.now().isoformat()
    
    # Find announcements that are currently active
    announcements = list(announcements_collection.find({}))
    
    active_announcements = []
    for announcement in announcements:
        # Check if announcement is within active date range
        start_date = announcement.get("start_date")
        expiration_date = announcement.get("expiration_date")
        
        # If start_date is set and current time is before start, skip
        if start_date and now < start_date:
            continue
        
        # If expiration_date is set and current time is after expiration, skip
        if expiration_date and now > expiration_date:
            continue
        
        # Convert ObjectId to string for JSON serialization
        announcement["_id"] = str(announcement["_id"])
        active_announcements.append(announcement)
    
    return active_announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (for management interface) - requires authentication"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    announcements = list(announcements_collection.find({}))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.post("")
def create_announcement(announcement: AnnouncementCreate, username: str) -> Dict[str, Any]:
    """Create a new announcement - requires authentication"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Create announcement document
    announcement_doc = {
        "message": announcement.message,
        "start_date": announcement.start_date,
        "expiration_date": announcement.expiration_date,
        "created_by": username,
        "created_at": datetime.now().isoformat()
    }
    
    result = announcements_collection.insert_one(announcement_doc)
    announcement_doc["_id"] = str(result.inserted_id)
    
    return announcement_doc


@router.put("/{announcement_id}")
def update_announcement(
    announcement_id: str, 
    announcement: AnnouncementUpdate, 
    username: str
) -> Dict[str, Any]:
    """Update an announcement - requires authentication"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Build update document
    update_doc = {}
    if announcement.message is not None:
        update_doc["message"] = announcement.message
    if announcement.start_date is not None:
        update_doc["start_date"] = announcement.start_date
    if announcement.expiration_date is not None:
        update_doc["expiration_date"] = announcement.expiration_date
    
    if not update_doc:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_doc["updated_at"] = datetime.now().isoformat()
    update_doc["updated_by"] = username
    
    # Update the announcement
    from bson import ObjectId
    result = announcements_collection.update_one(
        {"_id": ObjectId(announcement_id)},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    # Return updated announcement
    updated = announcements_collection.find_one({"_id": ObjectId(announcement_id)})
    if updated:
        updated["_id"] = str(updated["_id"])
    
    return updated


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement - requires authentication"""
    # Verify user is authenticated
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Delete the announcement
    from bson import ObjectId
    result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
