# ai_service/services/agent_config.py
"""
Fetches live agent configuration from Django.
Cached for 30 seconds to avoid hammering the DB on every agent call.
"""
import time
import httpx
from decouple import config

_DJANGO_URL = config("DJANGO_INTERNAL_URL", default="http://localhost:8000")
_API_KEY    = config("AI_SERVICE_API_KEY", default="internal-ai-key-change-this")

_cache = {}
_cache_time = 0
_CACHE_TTL = 2  # seconds


def get_agent_config(agent_id: str) -> dict:
    """
    Returns: {agent_id, llm_enabled, is_paused, pause_reason, confidence_threshold, model_override}
    Falls back to .env defaults if Django is unreachable.
    """
    global _cache, _cache_time

    if time.time() - _cache_time > _CACHE_TTL:
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(
                    f"{_DJANGO_URL}/api/audit/agent-config/",
                    headers={"X-API-Key": _API_KEY}
                )
                response.raise_for_status()
                _cache = {row["agent_id"]: row for row in response.json()}
                _cache_time = time.time()
        except Exception:
            pass  # Use stale cache or .env fallback below

    if agent_id in _cache:
        return _cache[agent_id]

    # Fallback to .env if Django unreachable
    flag_map = {
        "A1": "A1_USE_LLM", "A2": "A2_USE_LLM", "A3": "A3_USE_LLM",
        "A4": "A4_USE_LLM", "A5": "A5_USE_LLM", "A6": "A6_USE_LLM",
    }
    return {
        "agent_id": agent_id,
        "llm_enabled": config(flag_map.get(agent_id, ""), default=False, cast=bool),
        "is_paused": False,
        "pause_reason": "",
        "confidence_threshold": 0.65,
        "model_override": "",
        "fallback_behavior": "RULE_FALLBACK",
        "daily_token_budget": None,
    }
