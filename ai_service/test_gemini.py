# test_gemini.py
from services.gemini_client import call_gemini


def main():
    try:
        result = call_gemini(
            "You are a test assistant.",
            'Return JSON: {"status": "ok"}',
        )
    except Exception as exc:
        print(f"Gemini call failed: {exc}")
        return 1

    print("Gemini response:")
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())