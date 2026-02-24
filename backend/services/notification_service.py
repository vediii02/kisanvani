"""
Notifications and Alerts Service
SMS, WhatsApp, Email notifications for farmers and admins
"""

import os
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationType(str, Enum):
    SMS = "sms"
    WHATSAPP = "whatsapp"
    EMAIL = "email"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationService:
    """Unified notification service for SMS, WhatsApp, Email"""
    
    def __init__(self):
        # Exotel SMS
        self.exotel_sid = os.getenv("EXOTEL_SID", "")
        self.exotel_api_key = os.getenv("EXOTEL_API_KEY", "")
        self.exotel_api_token = os.getenv("EXOTEL_API_TOKEN", "")
        self.exotel_sms_url = f"https://api.exotel.com/v1/Accounts/{self.exotel_sid}/Sms/send.json"
        
        # WhatsApp (via Twilio/Gupshup)
        self.whatsapp_api_key = os.getenv("WHATSAPP_API_KEY", "")
        self.whatsapp_api_url = os.getenv("WHATSAPP_API_URL", "")
        
        # Email (via SMTP/SendGrid)
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY", "")
        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")
        
        self.use_mock = os.getenv("USE_MOCK_NOTIFICATIONS", "true").lower() == "true"
    
    async def send_notification(
        self,
        notification_type: NotificationType,
        recipient: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send notification via specified channel
        
        Args:
            notification_type: SMS, WhatsApp, or Email
            recipient: Phone number or email address
            message: Message content
            priority: Notification priority
            metadata: Additional data (template_id, etc.)
            
        Returns:
            {
                "success": bool,
                "message_id": str,
                "status": str,
                "error": Optional[str]
            }
        """
        if self.use_mock:
            return self._mock_send(notification_type, recipient, message)
        
        try:
            if notification_type == NotificationType.SMS:
                return await self.send_sms(recipient, message, metadata)
            elif notification_type == NotificationType.WHATSAPP:
                return await self.send_whatsapp(recipient, message, metadata)
            elif notification_type == NotificationType.EMAIL:
                return await self.send_email(recipient, message, metadata)
            else:
                return {
                    "success": False,
                    "message_id": None,
                    "status": "failed",
                    "error": f"Unknown notification type: {notification_type}"
                }
                
        except Exception as e:
            logger.error(f"Notification failed: {e}", exc_info=True)
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def send_sms(
        self,
        phone_number: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send SMS via Exotel"""
        try:
            # Exotel requires 10-digit number without country code
            phone_clean = phone_number.replace("+91", "").replace("+", "")
            
            data = {
                "From": metadata.get("from_number") if metadata else self.exotel_sid,
                "To": phone_clean,
                "Body": message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.exotel_sms_url,
                    auth=(self.exotel_api_key, self.exotel_api_token),
                    data=data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    sms_data = result.get("SMSMessage", {})
                    
                    return {
                        "success": True,
                        "message_id": sms_data.get("Sid"),
                        "status": sms_data.get("Status", "queued"),
                        "error": None
                    }
                else:
                    logger.error(f"SMS API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "message_id": None,
                        "status": "failed",
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"SMS send failed: {e}", exc_info=True)
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def send_whatsapp(
        self,
        phone_number: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send WhatsApp message"""
        try:
            # Format for WhatsApp API
            phone_formatted = phone_number if phone_number.startswith("+") else f"+{phone_number}"
            
            payload = {
                "phone": phone_formatted,
                "message": message
            }
            
            # Add template if provided
            if metadata and metadata.get("template_id"):
                payload["template_id"] = metadata["template_id"]
                payload["template_params"] = metadata.get("template_params", [])
            
            headers = {
                "Authorization": f"Bearer {self.whatsapp_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.whatsapp_api_url,
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    return {
                        "success": True,
                        "message_id": result.get("message_id"),
                        "status": result.get("status", "sent"),
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "message_id": None,
                        "status": "failed",
                        "error": f"API error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"WhatsApp send failed: {e}", exc_info=True)
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def send_email(
        self,
        email_address: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send email via SendGrid or SMTP"""
        try:
            subject = metadata.get("subject", "किसान वाणी सूचना") if metadata else "किसान वाणी सूचना"
            
            if self.sendgrid_api_key:
                return await self._send_email_sendgrid(email_address, subject, message, metadata)
            else:
                return await self._send_email_smtp(email_address, subject, message, metadata)
                
        except Exception as e:
            logger.error(f"Email send failed: {e}", exc_info=True)
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_email_sendgrid(
        self,
        to_email: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send email via SendGrid API"""
        try:
            url = "https://api.sendgrid.com/v3/mail/send"
            
            payload = {
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": metadata.get("from_email", "noreply@kisanvani.com") if metadata else "noreply@kisanvani.com"},
                "subject": subject,
                "content": [{"type": "text/plain", "value": message}]
            }
            
            headers = {
                "Authorization": f"Bearer {self.sendgrid_api_key}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers, timeout=30.0)
                
                if response.status_code == 202:
                    return {
                        "success": True,
                        "message_id": response.headers.get("X-Message-Id"),
                        "status": "sent",
                        "error": None
                    }
                else:
                    return {
                        "success": False,
                        "message_id": None,
                        "status": "failed",
                        "error": f"SendGrid error: {response.status_code}"
                    }
                    
        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    async def _send_email_smtp(
        self,
        to_email: str,
        subject: str,
        message: str,
        metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Send email via SMTP"""
        try:
            import aiosmtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg["From"] = metadata.get("from_email", self.smtp_user) if metadata else self.smtp_user
            msg["To"] = to_email
            msg["Subject"] = subject
            
            msg.attach(MIMEText(message, "plain", "utf-8"))
            
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_pass,
                use_tls=True
            )
            
            return {
                "success": True,
                "message_id": f"smtp_{datetime.utcnow().timestamp()}",
                "status": "sent",
                "error": None
            }
            
        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return {
                "success": False,
                "message_id": None,
                "status": "failed",
                "error": str(e)
            }
    
    def _mock_send(
        self,
        notification_type: NotificationType,
        recipient: str,
        message: str
    ) -> Dict[str, Any]:
        """Mock notification for testing"""
        import uuid
        
        logger.info(f"[MOCK] {notification_type.upper()} to {recipient}: {message[:50]}...")
        
        return {
            "success": True,
            "message_id": f"MOCK_{uuid.uuid4().hex[:16]}",
            "status": "sent",
            "error": None
        }
    
    # Predefined templates
    async def send_welcome_message(self, phone_number: str, farmer_name: Optional[str] = None) -> Dict[str, Any]:
        """Send welcome message to new farmer"""
        name = farmer_name or "किसान भाई"
        message = f"नमस्ते {name}! किसान वाणी में आपका स्वागत है। अब आप अपनी खेती की समस्या के लिए हमें कॉल कर सकते हैं।"
        
        return await self.send_notification(NotificationType.SMS, phone_number, message)
    
    async def send_case_resolved(self, phone_number: str, case_id: int) -> Dict[str, Any]:
        """Notify farmer about case resolution"""
        message = f"आपकी समस्या #{case_id} का समाधान हो गया है। विस्तार से जानकारी के लिए कॉल करें।"
        
        return await self.send_notification(NotificationType.SMS, phone_number, message)
    
    async def send_follow_up_reminder(self, phone_number: str, days_since_call: int) -> Dict[str, Any]:
        """Send follow-up reminder"""
        message = f"नमस्ते! {days_since_call} दिन पहले आपने समस्या बताई थी। क्या समाधान मिला? फीडबैक देने के लिए कॉल करें।"
        
        return await self.send_notification(NotificationType.SMS, phone_number, message)
    
    async def send_bulk_notification(
        self,
        recipients: List[str],
        message: str,
        notification_type: NotificationType = NotificationType.SMS
    ) -> Dict[str, Any]:
        """Send bulk notifications"""
        results = {
            "total": len(recipients),
            "success": 0,
            "failed": 0,
            "details": []
        }
        
        for recipient in recipients:
            result = await self.send_notification(notification_type, recipient, message)
            
            if result["success"]:
                results["success"] += 1
            else:
                results["failed"] += 1
            
            results["details"].append({
                "recipient": recipient,
                "success": result["success"],
                "message_id": result.get("message_id"),
                "error": result.get("error")
            })
        
        return results


# Global instance
notification_service = NotificationService()
