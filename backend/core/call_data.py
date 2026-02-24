"""
CallData is the standard internal structure for all call records.
All provider adapters must normalize their payloads to this format.

Fields:
- provider_name: str
- provider_call_id: str
- status: str (ACTIVE, COMPLETED, FAILED)
- from_phone: str
- to_phone: str
- start_time: datetime
- end_time: datetime or None
- duration_seconds: int or None

Backward compatibility: Existing DB columns (exotel_call_sid, etc.) are preserved. provider_call_id is the universal key for all providers.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CallData:
    provider_name: str
    provider_call_id: str
    status: str
    from_phone: str
    to_phone: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
