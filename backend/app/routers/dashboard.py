from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, PatientCase, Analysis, ClinicianReview
from app.schemas import DashboardSummary
from app.utils import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_cases = db.query(PatientCase).filter(PatientCase.user_id == current_user.id).count()
    total_analyses = db.query(Analysis).join(PatientCase).filter(PatientCase.user_id == current_user.id).count()

    # Pending reviews = analyses without a clinician review
    reviewed_ids = db.query(ClinicianReview.analysis_id).subquery()
    pending = db.query(Analysis).join(PatientCase).filter(
        PatientCase.user_id == current_user.id,
        ~Analysis.id.in_(db.query(ClinicianReview.analysis_id))
    ).count()

    # AI agreement rate
    total_reviews = db.query(ClinicianReview).join(Analysis).join(PatientCase).filter(
        PatientCase.user_id == current_user.id
    ).count()
    agreed = db.query(ClinicianReview).join(Analysis).join(PatientCase).filter(
        PatientCase.user_id == current_user.id,
        ClinicianReview.agrees_with_ai == True
    ).count()
    agreement_rate = (agreed / total_reviews * 100) if total_reviews > 0 else 0

    # Cases by module
    chest = db.query(Analysis).join(PatientCase).filter(
        PatientCase.user_id == current_user.id, Analysis.module == "chest_xray"
    ).count()
    skin = db.query(Analysis).join(PatientCase).filter(
        PatientCase.user_id == current_user.id, Analysis.module == "skin_lesion"
    ).count()
    retinal = db.query(Analysis).join(PatientCase).filter(
        PatientCase.user_id == current_user.id, Analysis.module == "retinal"
    ).count()

    # Recent analyses
    recent = db.query(Analysis).join(PatientCase).filter(
        PatientCase.user_id == current_user.id
    ).order_by(Analysis.created_at.desc()).limit(5).all()

    recent_list = [
        {
            "id": a.id,
            "module": a.module,
            "predicted_class": a.predicted_class,
            "confidence": a.confidence_score,
            "created_at": a.created_at.isoformat(),
        }
        for a in recent
    ]

    return DashboardSummary(
        total_cases=total_cases,
        total_analyses=total_analyses,
        pending_reviews=pending,
        ai_agreement_rate=round(agreement_rate, 1),
        cases_by_module={"chest_xray": chest, "skin_lesion": skin, "retinal": retinal},
        recent_analyses=recent_list,
    )
