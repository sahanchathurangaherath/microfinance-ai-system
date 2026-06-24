from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from agents.data_collection_agent import DataCollectionAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.recommendation_agent import RecommendationAgent
from agents.monitoring_agent import MonitoringAgent
from agents.fraud_detection_agent import FraudDetectionAgent
from agents.communication_agent import CommunicationAgent

from pydantic import BaseModel
from typing import Dict, Any, Optional,List
from decouple import config
import httpx

app = FastAPI(
    title="Microfinance AI Agent Service",
    description="AI agents for risk assessment, recommendation, fraud detection, and monitoring.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = config('AI_SERVICE_API_KEY', default='internal-ai-key-change-this')




def verify_api_key(x_api_key: str = Header(...)):
    """All requests from Django """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    


class A1ValidateRequest(BaseModel):
    client_id: int
    client_data: Dict[str, Any]
    kyc_data: Dict[str, Any]


class A2RiskRequest(BaseModel):
    loan_id: int
    client_data: Dict[str, Any]
    loan_data: Dict[str, Any]
    repayment_history: Optional[Dict[str, Any]] = {}



class A3RecommendationRequest(BaseModel):
    loan_id: int
    risk_score: float
    risk_category: str
    default_signals: list = []
    kyc_score: float = 0
    requested_amount: float
    monthly_income: float
    requested_duration_months: int
    debt_to_income_ratio: float = 0
    has_repayment_history: bool = False
    ai_rationale: str = ""


class InstallmentData(BaseModel):#A4 input structure for repayment monitoring
    installment_id: int
    installment_number: int
    due_date: str
    amount_due: float
    outstanding: float
    status: str

class LoanRepaymentData(BaseModel):#A4 input structure for repayment monitoring
    loan_id: int
    loan_number: str
    installments: List[InstallmentData]

class A4ScanRequest(BaseModel):
    loans: List[LoanRepaymentData]
    today: Optional[str] = None


class A5FraudRequest(BaseModel):
    check_type: str = "FULL"
    client_id: Optional[int] = None
    loan_id: Optional[int] = None
    identity_data: Dict[str, Any] = {}
    application_data: Dict[str, Any] = {}
    payment_data: Dict[str, Any] = {}
    kyc_data: Dict[str, Any] = {}

class A6DraftRequest(BaseModel):
    comm_type: str
    context: Dict[str, Any]
    channels: List[str] = ["SMS", "EMAIL"]





@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Microfinance AI Agent Service",
        "agents": ["A1", "A2", "A3", "A4", "A5", "A6"]
    }


@app.get("/agents")
def list_agents():
    return {
        "agents": [
            {"id": "A1", "name": "Data Collection Agent", "status": "active"},
            {"id": "A2", "name": "Risk Assessment Agent", "status": "active"},
            {"id": "A3", "name": "Recommendation Agent", "status": "active"},
            {"id": "A4", "name": "Monitoring Agent", "status": "active"},
            {"id": "A5", "name": "Fraud Detection Agent", "status": "active"},
            {"id": "A6", "name": "Communication Agent", "status": "active"},
        ]
    }

@app.post("/api/a1/validate-client")
def validate_client(request: A1ValidateRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    agent = DataCollectionAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a2/risk-score")
def risk_score(request: A2RiskRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    agent = RiskAssessmentAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a3/recommendation")
def get_recommendation(request: A3RecommendationRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    agent = RecommendationAgent()
    result = agent.run(request.dict())
    return result

@app.post("/api/a4/check-repayments")
def check_repayments(request: A4ScanRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    agent = MonitoringAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a5/fraud-check")
def fraud_check(request: A5FraudRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    agent = FraudDetectionAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a6/draft-message")
def draft_message(request: A6DraftRequest, x_api_key: str = Header(...)):
    verify_api_key(x_api_key)
    agent = CommunicationAgent()
    result = agent.run(request.dict())
    return result