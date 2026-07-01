from fastapi import FastAPI, Header, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from agents.data_collection_agent import DataCollectionAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.recommendation_agent import RecommendationAgent
from agents.monitoring_agent import MonitoringAgent
from agents.fraud_detection_agent import FraudDetectionAgent
from agents.communication_agent import CommunicationAgent
from schemas.requests import (
    A1ValidateRequest,
    A2RiskRequest,
    A3RecommendationRequest,
    A4ScanRequest,
    A5FraudRequest,
    A6DraftRequest,
)
from decouple import config

app = FastAPI(
    title="Microfinance AI Agent Service",
    description="AI agents for risk assessment, recommendation, fraud detection, and monitoring.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = config('AI_SERVICE_API_KEY', default='internal-ai-key-change-this')


def verify_api_key(x_api_key: str = Header(...)):
    """All requests from Django """
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")



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

from agents.recommendation_agent import USE_LLM
@app.get("/debug")
def debug_info():
    import sys
    return {"USE_LLM": USE_LLM, "sys.path": sys.path}

@app.post("/api/a1/validate-client")
def validate_client(request: A1ValidateRequest, _=Depends(verify_api_key)):
    agent = DataCollectionAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a2/risk-score")
def risk_score(request: A2RiskRequest, _=Depends(verify_api_key)):
    agent = RiskAssessmentAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a3/recommendation")
def get_recommendation(request: A3RecommendationRequest, _=Depends(verify_api_key)):
    agent = RecommendationAgent()
    result = agent.run(request.dict())
    return result

@app.post("/api/a4/check-repayments")
def check_repayments(request: A4ScanRequest, _=Depends(verify_api_key)):
    agent = MonitoringAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a5/fraud-check")
def fraud_check(request: A5FraudRequest, _=Depends(verify_api_key)):
    agent = FraudDetectionAgent()
    result = agent.run(request.dict())
    return result


@app.post("/api/a6/draft-message")
def draft_message(request: A6DraftRequest, _=Depends(verify_api_key)):
    agent = CommunicationAgent()
    result = agent.run(request.dict())
    return result