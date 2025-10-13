from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class DocumentBase(BaseModel):
    kind: str
    title: str
    path: str
    meta_json: Optional[Dict[str, Any]] = None


class DocumentCreate(DocumentBase):
    pass


class Document(DocumentBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class RequirementBase(BaseModel):
    code: str
    text: str
    category: Optional[str] = None
    priority: str = "medium"


class RequirementCreate(RequirementBase):
    rfq_id: int


class Requirement(RequirementBase):
    id: int
    rfq_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class EvidenceBase(BaseModel):
    snippet: str
    score: float = 0.0
    evidence_type: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    requirement_id: int
    source_doc_id: int


class Evidence(EvidenceBase):
    id: int
    requirement_id: int
    source_doc_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class FacilityFeatureBase(BaseModel):
    name: str
    value: Optional[str] = None


class FacilityFeatureCreate(FacilityFeatureBase):
    source_doc_id: int


class FacilityFeature(FacilityFeatureBase):
    id: int
    source_doc_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class PricingItemBase(BaseModel):
    name: str
    description: Optional[str] = None
    qty: float = 1.0
    unit: Optional[str] = None
    unit_price: float
    category: Optional[str] = None


class PricingItemCreate(PricingItemBase):
    rfq_id: int


class PricingItem(PricingItemBase):
    id: int
    rfq_id: int
    total_price: Optional[float] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ComplianceMatrixItem(BaseModel):
    requirement: Requirement
    evidence: List[Evidence]
    risk_level: str  # low, medium, high, critical
    gap_analysis: Optional[str] = None
    mitigation: Optional[str] = None


class ComplianceMatrix(BaseModel):
    rfq_id: int
    items: List[ComplianceMatrixItem]
    overall_risk: str
    total_requirements: int
    met_requirements: int
    gap_requirements: int


class ProposalDraft(BaseModel):
    rfq_id: int
    executive_summary: str
    technical_approach: str
    past_performance: str
    pricing_summary: str
    compliance_matrix: ComplianceMatrix
    created_at: datetime


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"

