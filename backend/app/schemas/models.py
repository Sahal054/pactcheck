from pydantic import BaseModel, Field
from typing import Literal, Optional

Risk = Literal["Low", "Medium", "High", "Unclear"]
ComplianceStatus = Literal[
    "Compliant", "Partially Compliant", "Non-Compliant", "Not Assessed"
]


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


class LLMClauseEvaluation(BaseModel):
    risk_level: Risk
    compliance_status: ComplianceStatus
    applicable_rule_ids: list[str] = Field(default_factory=list)
    explanation: str = Field(
        description="Plain-English explanation of commercial exposure and policy gap"
    )
    suggested_redline: Optional[str] = Field(
        default=None,
        description="Drop-in replacement clause aligned with company policy, or null if Compliant",
    )
    negotiation_action: str = Field(default="Needs legal review")
    counterparty_pushback_email: Optional[str] = Field(
        default=None,
        description="1-2 sentence polite legal justification email to send to vendor counsel",
    )
    requires_legal_review: bool = True


class ClauseUpdateRequest(BaseModel):
    redline_status: Literal["pending", "accepted", "edited", "rejected"] = "accepted"
    suggested_redline: Optional[str] = None


class SettingsUpdate(BaseModel):
    llm_provider: Optional[Literal["mock", "openai", "openrouter"]] = None
    llm_model: Optional[str] = None
    embedding_provider: Optional[Literal["local", "openai", "openrouter"]] = None
    embedding_model: Optional[str] = None
    openai_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
