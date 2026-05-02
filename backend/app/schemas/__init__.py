from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime


# ── Auth ──
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    specialty: str = ""
    organization: str = ""
    license_number: str = ""


class UserLogin(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    email: str
    full_name: str
    role: str
    specialty: str
    organization: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ── Patient Cases ──
class CaseCreate(BaseModel):
    patient_id: str = ""
    patient_age: Optional[int] = None
    patient_gender: str = ""
    chief_complaint: str = ""
    clinical_notes: str = ""


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    user_id: int
    patient_id: str
    patient_age: Optional[int]
    patient_gender: str
    chief_complaint: str
    clinical_notes: str
    status: str
    created_at: datetime
    image_count: int = 0
    analysis_count: int = 0


class CaseDetailResponse(CaseResponse):
    images: List["ImageResponse"] = []


# ── Medical Images ──
class ImageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    case_id: int
    image_type: str
    original_filename: str
    upload_date: datetime


# ── Analysis ──
class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    image_id: int
    case_id: int
    module: str
    model_name: str
    predicted_class: str
    confidence_score: float
    all_predictions: Dict[str, Any]
    gradcam_path: str
    processing_time_ms: int
    created_at: datetime
    interpretation: Optional["InterpretationResponse"] = None
    review: Optional["ReviewResponse"] = None


# ── Clinical Interpretation ──
class InterpretationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    analysis_id: int
    clinical_summary: str
    differential_diagnosis: str
    recommendations: str
    created_at: datetime


# ── Clinician Review ──
class ReviewCreate(BaseModel):
    agrees_with_ai: bool = True
    clinician_diagnosis: str = ""
    clinical_notes: str = ""
    action_taken: str = "confirm"


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    analysis_id: int
    reviewer_id: int
    agrees_with_ai: bool
    clinician_diagnosis: str
    clinical_notes: str
    action_taken: str
    created_at: datetime


# ── Diagnostic Reports ──
class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())
    id: int
    case_id: int
    content_markdown: str
    generated_by: str
    review_status: str
    created_at: datetime


# ── Dashboard ──
class DashboardSummary(BaseModel):
    total_cases: int = 0
    total_analyses: int = 0
    pending_reviews: int = 0
    ai_agreement_rate: float = 0.0
    cases_by_module: Dict[str, int] = {}
    recent_analyses: List[Dict[str, Any]] = []
