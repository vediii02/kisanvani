"""
TwilioCallProvider and ExotelCallProvider implement CallProviderInterface.
Each adapter converts provider-specific payloads/statuses to the standard CallData format.

Adapter Pattern:
---------------
These adapters allow switching telephony providers via environment variable only. No code changes are needed for switching.
To add a new provider, implement CallProviderInterface and update CallProviderFactory.
Backward compatibility: Existing Exotel data and DB columns remain valid. provider_call_id is used as the universal key.
"""
from .call_provider_interface import CallProviderInterface
from typing import Any, Dict
from datetime import datetime

class TwilioCallProvider(CallProviderInterface):
    def parse_incoming_call(self, payload: Dict[str, Any]):
        # Twilio payload normalization
        return {
            'provider_name': 'twilio',
            'provider_call_id': payload.get('CallSid'),
            'status': self._map_status(payload.get('CallStatus')),
            'from_phone': payload.get('From'),
            'to_phone': payload.get('To'),
            'start_time': payload.get('StartTime', datetime.utcnow()),
            'end_time': None,
            'duration_seconds': None,
        }

    def parse_status_callback(self, payload: Dict[str, Any]):
        return {
            'provider_name': 'twilio',
            'provider_call_id': payload.get('CallSid'),
            'status': self._map_status(payload.get('CallStatus')),
            'from_phone': payload.get('From'),
            'to_phone': payload.get('To'),
            'start_time': payload.get('StartTime', datetime.utcnow()),
            'end_time': payload.get('EndTime', datetime.utcnow()),
            'duration_seconds': payload.get('Duration'),
        }

    def _map_status(self, status):
        # Twilio status mapping
        if status in ['in-progress', 'ringing', 'queued']:
            return 'ACTIVE'
        elif status in ['completed']:
            return 'COMPLETED'
        elif status in ['failed', 'busy', 'no-answer', 'canceled']:
            return 'FAILED'
        return 'UNKNOWN'

class ExotelCallProvider(CallProviderInterface):
    def parse_incoming_call(self, payload: Dict[str, Any]):
        # Exotel payload normalization
        return {
            'provider_name': 'exotel',
            'provider_call_id': payload.get('CallSid') or payload.get('Sid'),
            'status': self._map_status(payload.get('Status')),
            'from_phone': payload.get('From'),
            'to_phone': payload.get('To'),
            'start_time': payload.get('StartTime', datetime.utcnow()),
            'end_time': None,
            'duration_seconds': None,
        }

    def parse_status_callback(self, payload: Dict[str, Any]):
        return {
            'provider_name': 'exotel',
            'provider_call_id': payload.get('CallSid') or payload.get('Sid'),
            'status': self._map_status(payload.get('Status')),
            'from_phone': payload.get('From'),
            'to_phone': payload.get('To'),
            'start_time': payload.get('StartTime', datetime.utcnow()),
            'end_time': payload.get('EndTime', datetime.utcnow()),
            'duration_seconds': payload.get('Duration'),
        }

    def _map_status(self, status):
        # Exotel status mapping
        if status in ['in-progress', 'ringing', 'queued']:
            return 'ACTIVE'
        elif status in ['completed']:
            return 'COMPLETED'
        elif status in ['failed', 'busy', 'no-answer', 'canceled']:
            return 'FAILED'
        return 'UNKNOWN'
