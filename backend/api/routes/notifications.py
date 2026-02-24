"""
Notifications API Routes
Send and manage notifications
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from services.notification_service import notification_service, NotificationType, NotificationPriority

router = APIRouter()


class NotificationRequest(BaseModel):
    notification_type: NotificationType
    recipient: str
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM
    metadata: Optional[dict] = None


class BulkNotificationRequest(BaseModel):
    notification_type: NotificationType
    recipients: List[str]
    message: str
    priority: NotificationPriority = NotificationPriority.MEDIUM


@router.post("/send")
async def send_notification(request: NotificationRequest):
    """Send single notification"""
    result = await notification_service.send_notification(
        notification_type=request.notification_type,
        recipient=request.recipient,
        message=request.message,
        priority=request.priority,
        metadata=request.metadata
    )
    
    return result


@router.post("/send-bulk")
async def send_bulk_notification(request: BulkNotificationRequest):
    """Send bulk notifications"""
    if len(request.recipients) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 recipients allowed")
    
    result = await notification_service.send_bulk_notification(
        recipients=request.recipients,
        message=request.message,
        notification_type=request.notification_type
    )
    
    return result


@router.post("/welcome/{phone_number}")
async def send_welcome(phone_number: str, farmer_name: Optional[str] = None):
    """Send welcome message to new farmer"""
    result = await notification_service.send_welcome_message(
        phone_number=phone_number,
        farmer_name=farmer_name
    )
    
    return result


@router.post("/case-resolved/{phone_number}/{case_id}")
async def notify_case_resolved(phone_number: str, case_id: int):
    """Notify farmer about case resolution"""
    result = await notification_service.send_case_resolved(
        phone_number=phone_number,
        case_id=case_id
    )
    
    return result


@router.post("/follow-up/{phone_number}")
async def send_follow_up(phone_number: str, days_since_call: int):
    """Send follow-up reminder"""
    result = await notification_service.send_follow_up_reminder(
        phone_number=phone_number,
        days_since_call=days_since_call
    )
    
    return result
