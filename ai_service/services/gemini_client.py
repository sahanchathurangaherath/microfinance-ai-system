
import json
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential
from decouple import config


_API_KEY     = config("GEMINI_API_KEY",   default="")
_MODEL_NAME  = config("LLM_MODEL",        default="gemini-2.0-flash")
_TEMPERATURE = config("LLM_TEMPERATURE",  default=0.1,  cast=float)
_MAX_TOKENS  = config("LLM_MAX_TOKENS",   default=2000, cast=int)

# One client instance reused across all calls
_client = genai.Client(api_key=_API_KEY)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def call_gemini(system_prompt: str, user_prompt: str) -> tuple:
    """
    Call Gemini and return parsed JSON output with usage metadata.
    Retries up to 3 times on failure with exponential backoff.
    Returns: (parsed_json_output, usage_metadata_dict)
    usage_metadata contains: prompt_tokens, completion_tokens, model_used
    Raises ValueError if output cannot be parsed as JSON.
    """
    response = _client.models.generate_content(
        model=_MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=_TEMPERATURE,
            max_output_tokens=_MAX_TOKENS,
            response_mime_type="application/json",
        ),
    )

    raw_text = response.text.strip()

    # Strip markdown code fences if model adds them anyway
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Gemini returned non-JSON output: {raw_text[:200]}") from e

    # Extract token usage if available
    usage = {}
    try:
        meta = response.usage_metadata
        usage = {
            "prompt_tokens": getattr(meta, "prompt_token_count", 0),
            "completion_tokens": getattr(meta, "candidates_token_count", 0),
            "model_used": _MODEL_NAME,
        }
    except Exception:
        usage = {"prompt_tokens": 0, "completion_tokens": 0, "model_used": _MODEL_NAME}

    return parsed, usage
