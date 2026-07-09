# ai_service/services/face_matcher.py
"""
Local face comparison using DeepFace.
Runs on CPU — no GPU required. ~2-3 seconds per comparison.
Result is ADVISORY ONLY — never auto-rejects a client.
"""

from decouple import config

try:
    from deepface import DeepFace
except ImportError:
    DeepFace = None

_ENABLED = config("A1_FACE_MATCH_ENABLED", default=True, cast=bool)


def compare_faces(nic_photo_path: str, selfie_path: str) -> dict:
    """
    Compare NIC photo with client selfie.
    Returns match result and confidence.
    IMPORTANT: This is advisory only. Never auto-reject based on this alone.
    """
    if not _ENABLED:
        return {"face_match_available": False}

    try:
        from deepface import DeepFace

        result = DeepFace.verify(
            img1_path=nic_photo_path,
            img2_path=selfie_path,
            model_name="Facenet512",
            distance_metric="cosine",
            enforce_detection=False,  # Don't fail if face not detected
        )

        distance = result.get("distance", 1.0)
        verified = result.get("verified", False)

        # threshold: distance < 0.4 = clear match
        #                0.4-0.6 = uncertain, flag for human
        #                > 0.6 = likely mismatch, flag for human

        if distance < 0.4:
            match_status = "MATCH"
            flag = None
        elif distance < 0.6:
            match_status = "UNCERTAIN"
            flag = f"Face similarity uncertain (distance: {round(distance, 2)}) — manual review advised"
        else:
            match_status = "MISMATCH"
            flag = f"Face mismatch detected (distance: {round(distance, 2)}) — human verification required"

        return {
            "face_match_available": True,
            "match_status": match_status,
            "distance": round(distance, 3),
            "flag": flag,
        }

    except Exception as e:
        return {
            "face_match_available": False,
            "error": str(e)[:100],
        }
