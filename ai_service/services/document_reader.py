# ai_service/services/document_reader.py
"""
Document OCR for A1 KYC validation.
"""

import base64
import json
from pathlib import Path
import httpx
from decouple import config

_BASE_URL   = config("LOCAL_LLM_BASE_URL", default="http://localhost:11434")
_MODEL_NAME = config("LOCAL_LLM_MODEL",    default="qwen3:8b")
_ENABLED    = config("A1_OCR_ENABLED",     default=True, cast=bool)


def read_nic_document(file_path: str, form_data: dict) -> dict:
    """
    Extract text from NIC document image using Qwen3.5 (local Ollama) and compare with form data.
    Returns comparison result and any mismatch flags.
    """
    if not _ENABLED:
        return {"ocr_available": False, "flags": []}

    path = Path(file_path)
    if not path.exists():
        return {"ocr_available": False, "flags": ["Document file not found on disk"]}

    # Read and encode file to base64
    suffix = path.suffix.lower()
    if suffix not in ['.jpg', '.jpeg', '.png']:
        return {"ocr_available": False, "flags": [f"Local vision model only supports images (got {suffix})"]}

    try:
        with open(path, "rb") as f:
            file_data = base64.b64encode(f.read()).decode("utf-8")
    except Exception as e:
        return {"ocr_available": False, "flags": [f"Failed to read image file: {str(e)}"]}

    prompt = f"""You are a KYC document analyst.
Extract identity information from this Sri Lankan NIC document image.

Compare the extracted data with the form-submitted data:
Form Name: {form_data.get('first_name', '')} {form_data.get('last_name', '')}
Form NIC: {form_data.get('nic_number', '')}
Form DOB: {form_data.get('date_of_birth', '')}
Form Gender: {form_data.get('gender', '')}

Return ONLY this JSON structure:
{{
  "document_readable": true or false,
  "extracted_name": "name as it appears on document or null",
  "extracted_nic": "NIC number on document or null",
  "extracted_dob": "date of birth on document or null",
  "name_match": true or false or null,
  "nic_match": true or false or null,
  "dob_match": true or false or null,
  "document_appears_genuine": true or false,
  "flags": ["list any anomalies — tampering, blurring, mismatch details"],
  "confidence": 0.0 to 1.0
}}"""

    payload = {
        "model": _MODEL_NAME,
        "stream": False,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [file_data]
            }
        ],
        "format": "json"
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(f"{_BASE_URL}/api/chat", json=payload)
            response.raise_for_status()

        data     = response.json()
        raw_text = data.get("message", {}).get("content", "").strip()

        # Remove thinking blocks
        if "<think>" in raw_text and "</think>" in raw_text:
            raw_text = raw_text.split("</think>")[-1].strip()

        # Remove markdown fences
        if raw_text.startswith("```"):
            raw_text = raw_text.split("```")[1]
            if raw_text.startswith("json"):
                raw_text = raw_text[4:]
            raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        return parsed
    except Exception as e:
        return {
            "ocr_available": False,
            "flags": [f"OCR extraction failed: {str(e)[:100]}"],
            "document_readable": False
        }
