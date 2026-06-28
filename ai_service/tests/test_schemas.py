import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.requests import A1ValidateRequest, A6DraftRequest


class SchemaImportTests(unittest.TestCase):
    def test_request_models_can_be_instantiated(self):
        request = A1ValidateRequest(
            client_id=1,
            client_data={"name": "Test"},
            kyc_data={"status": "ok"},
        )
        self.assertEqual(request.client_id, 1)

        draft_request = A6DraftRequest(comm_type="SMS", context={"foo": "bar"})
        self.assertEqual(draft_request.comm_type, "SMS")


if __name__ == "__main__":
    unittest.main()
