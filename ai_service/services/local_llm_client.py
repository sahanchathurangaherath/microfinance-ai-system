"""
Ollama client for qwen3:8b 
"""

import json
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from decouple import config

_BASE_URL    = config("LOCAL_LLM_BASE_URL", default="http://localhost:11434")
_MODEL_NAME  = config("LOCAL_LLM_MODEL",    default="qwen3:8b")
_TEMPERATURE = config("LLM_TEMPERATURE",    default=0.1,  cast=float)
_MAX_TOKENS  = config("LLM_MAX_TOKENS",     default=2000, cast=int)

# A2, A3, A5 use deep thinking mode — slower but more accurate
_THINK_AGENTS = {"A2", "A3", "A5"}

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_local_llm(
    system_prompt: str,
    user_prompt: str,
    agent_id: str = ""
) -> tuple[dict, dict]:
    """
    Call qwen3:8b via Ollama.
    Returns: (parsed_json_dict, usage_metadata_dict)
    Retries 3 times on failure with exponential backoff.
    On total failure: raises exception → Manual Mode activates 
    """
    prefix       = "/think " if agent_id in _THINK_AGENTS else "/no_think "
    full_prompt  = prefix + user_prompt

    payload = {
        "model":  _MODEL_NAME,
        "stream": False,
        "options": {
            "temperature": _TEMPERATURE,
            "num_predict": _MAX_TOKENS,
        },
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": full_prompt},
        ],
        "format": "json",
    }

    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{_BASE_URL}/api/chat", json=payload)
        response.raise_for_status()

    data     = response.json()
    raw_text = data.get("message", {}).get("content", "").strip()

    # Remove qwen3 thinking block if present
    if "<think>" in raw_text and "</think>" in raw_text:
        raw_text = raw_text.split("</think>")[-1].strip()

    # Remove markdown fences
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"qwen3 returned non-JSON: {raw_text[:200]}") from e

    usage = {
        "prompt_tokens":     data.get("prompt_eval_count", 0),
        "completion_tokens": data.get("eval_count", 0),
        "model_used":        _MODEL_NAME,
    }

    return parsed, usage
