from pydantic import BaseModel, Field
from typing import Literal, Optional

Risk = Literal["Low", "Medium", "High", "Unclear"]

class PlaybookRule(BaseModel):
    rule_id: str
    clause_type: str
    policy: str
    red_flags: list[str] = []
    preferred_wording: str = ""
    fallback_wording: Optional[str] = None
    applicable_documents: list[str] = ["NDA", "MSA"]
    escalation_conditions: list[str] = []
    source: str = "Legal Negotiation Playbook"
    page: Optional[int] = None

class Clause(BaseModel):
    clause_id: str
    heading: str
    clause_number: Optional[str] = None
    text: str
    page_start: int = 1
    page_end: int = 1
    clause_type: str = "unknown"

class Assessment(BaseModel):
    clause_id: str
    heading: str
    risk_level: Risk
    compliance_status: str
    applicable_rule_ids: list[str] = []
    explanation: str
    original_text: str
    suggested_redline: Optional[str] = None
    negotiation_action: str = "Needs legal review"
    requires_legal_review: bool = True
    evidence: list[dict] = []

class ReviewRequest(BaseModel):
    document_type: Literal["NDA", "MSA"] = "MSA"

class SettingsUpdate(BaseModel):
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None
    embedding_provider: Optional[str] = None
    embedding_model: Optional[str] = None
