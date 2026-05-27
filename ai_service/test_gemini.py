# test_gemini.py
from services.gemini_client import call_gemini

result = call_gemini('You are a test assistant.', 'Return JSON: {"status": "ok"}')
print(result)