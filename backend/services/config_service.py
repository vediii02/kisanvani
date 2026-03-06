"""
Config Service — reads PlatformConfig from DB with caching.
Services call get_platform_config() to get current AI provider settings.
"""

import time
import logging
from typing import Optional
from sqlalchemy import select
from db.base import AsyncSessionLocal
from db.models.audit import PlatformConfig

logger = logging.getLogger(__name__)

# Cache
_config_cache: Optional[dict] = None
_cache_timestamp: float = 0
_CACHE_TTL_SECONDS = 30


async def get_platform_config() -> dict:
    """
    Read PlatformConfig from DB, cached for 30 seconds.
    Returns a dict with all config fields.
    """
    global _config_cache, _cache_timestamp

    now = time.time()
    if _config_cache is not None and (now - _cache_timestamp) < _CACHE_TTL_SECONDS:
        return _config_cache

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(PlatformConfig).limit(1))
            config = result.scalar_one_or_none()
            if not config:
                _config_cache = _default_config()
            else:
                _config_cache = {
                    "stt_provider": config.stt_provider or "sarvam",
                    "tts_provider": config.tts_provider or "sarvam",
                    "llm_model": config.llm_model or "groq",
                    "default_language": config.default_language or "hi",
                    "ai_confidence_threshold": config.ai_confidence_threshold or 70,
                    "rag_strictness_level": config.rag_strictness_level or "medium",
                    "rag_min_confidence": config.rag_min_confidence or 60,
                    "rag_max_results": config.rag_max_results or 5,
                    "max_call_duration_minutes": config.max_call_duration_minutes or 15,
                    "force_kb_approval": config.force_kb_approval if config.force_kb_approval is not None else True,
                    "enable_call_recording": config.enable_call_recording if config.enable_call_recording is not None else True,
                    "enable_auto_escalation": config.enable_auto_escalation if config.enable_auto_escalation is not None else True,
                    "max_concurrent_calls": config.max_concurrent_calls or 100,
                }
            _cache_timestamp = now
            logger.info(f"PlatformConfig loaded: llm={_config_cache['llm_model']}, stt={_config_cache['stt_provider']}, tts={_config_cache['tts_provider']}")
            return _config_cache

    except Exception as e:
        logger.error(f"Failed to read PlatformConfig, using defaults: {e}")
        if _config_cache is not None:
            return _config_cache
        return _default_config()


def invalidate_config_cache():
    """Force next call to get_platform_config() to re-read from DB."""
    global _config_cache, _cache_timestamp
    _config_cache = None
    _cache_timestamp = 0
    logger.info("PlatformConfig cache invalidated")


def _default_config() -> dict:
    return {
        "stt_provider": "sarvam",
        "tts_provider": "sarvam",
        "llm_model": "groq",
        "default_language": "hi",
        "ai_confidence_threshold": 70,
        "rag_strictness_level": "medium",
        "rag_min_confidence": 60,
        "rag_max_results": 5,
        "max_call_duration_minutes": 15,
        "force_kb_approval": True,
        "enable_call_recording": True,
        "enable_auto_escalation": True,
        "max_concurrent_calls": 100,
    }
