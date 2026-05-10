from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

