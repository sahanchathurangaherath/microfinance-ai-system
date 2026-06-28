from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class A1ValidateRequest(BaseModel):
    client_id: int
    client_data: Dict[str, Any]
    kyc_data: Dict[str, Any]


class A2RiskRequest(BaseModel):
    loan_id: int
    client_data: Dict[str, Any]
    loan_data: Dict[str, Any]
    repayment_history: Optional[Dict[str, Any]] = Field(default_factory=dict)


class A3RecommendationRequest(BaseModel):
    loan_id: int
    risk_score: float
    risk_category: str
    default_signals: list = Field(default_factory=list)
    kyc_score: float = 0
    requested_amount: float
    monthly_income: float
    requested_duration_months: int
    debt_to_income_ratio: float = 0
    has_repayment_history: bool = False
    ai_rationale: str = ""


class InstallmentData(BaseModel):
    installment_id: int
    installment_number: int
    due_date: str
    amount_due: float
    outstanding: float
    status: str


class LoanRepaymentData(BaseModel):
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
    identity_data: Dict[str, Any] = Field(default_factory=dict)
    application_data: Dict[str, Any] = Field(default_factory=dict)
    payment_data: Dict[str, Any] = Field(default_factory=dict)
    kyc_data: Dict[str, Any] = Field(default_factory=dict)


class A6DraftRequest(BaseModel):
    comm_type: str
    context: Dict[str, Any]
    channels: List[str] = Field(default_factory=lambda: ["SMS", "EMAIL"])
