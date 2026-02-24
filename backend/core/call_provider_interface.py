"""
CallProviderInterface defines the contract for all telephony provider adapters.
Each provider (Twilio, Exotel, etc.) must implement this interface.

Methods:
- parse_incoming_call: Parse incoming call payload to internal CallData
- parse_status_callback: Parse status callback payload to internal CallData

Adapter Pattern:
---------------
This interface enables provider-agnostic call handling. To add a new provider, implement this interface and register in CallProviderFactory.
No changes to AI or call flow logic are required for new providers.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

class CallProviderInterface(ABC):
    @abstractmethod
    def parse_incoming_call(self, payload: Dict[str, Any]):
        """
        Parse incoming call payload and return normalized CallData dict.
        """
        pass

    @abstractmethod
    def parse_status_callback(self, payload: Dict[str, Any]):
        """
        Parse call status callback payload and return normalized CallData dict.
        """
        pass
