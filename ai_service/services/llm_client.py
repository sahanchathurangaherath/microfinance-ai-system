"""
Unified LLM entry point.
All 6 agents import ONLY from here.
Changing LOCAL_LLM_MODEL in .env is the only config needed to switch models.
"""

from decouple import config

_USE_LOCAL = config("LOCAL_LLM_ENABLED", default=True, cast=bool)


def call_llm(
    system_prompt: str,
    user_prompt:   str,
    agent_id:      str = ""
) -> tuple[dict, dict]:
    """
    Single function called by all agents.
    Returns (parsed_json, usage_metadata).
    Failure after 3 retries → exception → Django creates ManualReviewCase.
    """
    if _USE_LOCAL:
        from .local_llm_client import call_local_llm
        return call_local_llm(system_prompt, user_prompt, agent_id)
    else:
        raise RuntimeError(
            "LOCAL_LLM_ENABLED=false but no cloud fallback configured. "
            "Set LOCAL_LLM_ENABLED=true or configure a fallback."
        )
