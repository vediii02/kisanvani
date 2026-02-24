"""
CallProviderFactory returns the correct provider adapter based on environment/config.
Set CALL_PROVIDER in .env to 'twilio' or 'exotel'.
Add new providers by updating the registry below.

Usage:
------
This factory enables provider selection via environment variable only. No conditional logic is needed in controllers.
To add a new provider, implement CallProviderInterface and add to PROVIDER_REGISTRY.
"""
import os
from .call_provider_adapters import TwilioCallProvider, ExotelCallProvider
from .call_provider_interface import CallProviderInterface

PROVIDER_REGISTRY = {
    'twilio': TwilioCallProvider,
    'exotel': ExotelCallProvider,
    # Add new providers here
}

def get_call_provider() -> CallProviderInterface:
    provider_name = os.getenv('CALL_PROVIDER', 'exotel').lower()
    provider_class = PROVIDER_REGISTRY.get(provider_name)
    if not provider_class:
        raise ValueError(f"Unknown call provider: {provider_name}")
    return provider_class()
