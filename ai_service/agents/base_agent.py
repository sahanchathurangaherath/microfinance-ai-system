from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

class BaseAgent(ABC):
    """
    All AI agents must inherit from this class.

    """

    def __init__(self, agent_id: str, agent_name: str):
        self.agent_id = agent_id
        self.agent_name = agent_name

    @abstractmethod
    def run(self, input_data: Dict) -> Dict:
        """Execute the agent's main task."""
        pass

    def build_response(
        self,
        output: Any,
        confidence: float,
        rationale: str,
        input_reference: str,
        status: str = "SUCCESS",
        usage_metadata: dict | None = None
    ) -> Dict:
        """
        Standard response format for every agent.
        This ensures every AI output is explainable and traceable.
        """
        response = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "timestamp": datetime.utcnow().isoformat(),
            "status": status,
            "confidence": confidence,        # 0.0 to 1.0
            "rationale": rationale,          # Human-readable explanation
            "input_reference": input_reference,
            "output": output,
        }
        if usage_metadata is not None:
            response["usage_metadata"] = usage_metadata
        return response

    def low_confidence_response(self, input_reference: str, reason: str) -> Dict:
       
        return self.build_response(
            output=None,
            confidence=0.0,
            rationale=f"LOW CONFIDENCE - Human review required. Reason: {reason}",
            input_reference=input_reference,
            status="REQUIRES_HUMAN_REVIEW"
        )