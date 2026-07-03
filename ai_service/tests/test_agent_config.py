import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.agent_config import get_agent_config

class AgentConfigTests(unittest.TestCase):
    def test_get_agent_config_fallback(self):
        # Force cache clear or offline simulation
        with patch('services.agent_config._cache', {}), \
             patch('services.agent_config._cache_time', 0), \
             patch('httpx.Client.get') as mock_get:
            
            # Simulate Django failure to trigger fallback
            mock_get.side_effect = Exception("Django offline")
            
            config_res = get_agent_config("A2")
            
            self.assertEqual(config_res["agent_id"], "A2")
            self.assertEqual(config_res["fallback_behavior"], "RULE_FALLBACK")
            self.assertIsNone(config_res["daily_token_budget"])
            self.assertFalse(config_res["is_paused"])
            self.assertEqual(config_res["confidence_threshold"], 0.65)

if __name__ == "__main__":
    unittest.main()
