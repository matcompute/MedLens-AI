import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, PatientCase, MedicalImage, Analysis, ClinicalInterpretation, ClinicianReview
from app.schemas import AnalysisResponse, ReviewCreate, ReviewResponse, InterpretationResponse
from app.utils import get_current_user
from app.services.ml_service import run_inference, MODEL_REGISTRY
from app.services.gradcam_service import generate_gradcam
from app.services.gemini_service import interpret_analysis
from app.config import settings

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analyze/{image_id}", response_model=AnalysisResponse, status_code=201)
def analyze_image(
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Run CNN inference + Grad-CAM + Gemini interpretation on a medical image."""
    image = db.query(MedicalImage).filter(MedicalImage.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    case = db.query(PatientCase).filter(
        PatientCase.id == image.case_id, PatientCase.user_id == current_user.id
    ).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    image_path = os.path.join(settings.UPLOAD_DIR, image.file_path)
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found on disk")

    module = image.image_type
    model_info = MODEL_REGISTRY.get(module, {"name": "ResNet50", "version": "1.0"})

    # Step 1: CNN Inference
    predictions, predicted_class, confidence, proc_time = run_inference(image_path, module)

    # Step 2: Grad-CAM heatmap
    try:
        gradcam_filename = generate_gradcam(image_path, module)
    except Exception as e:
        gradcam_filename = ""

    # Step 3: Save analysis
    analysis = Analysis(
        image_id=image_id,
        case_id=case.id,
        module=module,
        model_name=model_info["name"],
        model_version=model_info["version"],
        predicted_class=predicted_class,
        confidence_score=confidence,
        all_predictions=predictions,
        gradcam_path=gradcam_filename,
        processing_time_ms=proc_time,
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Step 4: Gemini clinical interpretation
    try:
        interp = interpret_analysis(
            module=module,
            predicted_class=predicted_class,
            confidence=confidence,
            all_predictions=predictions,
            patient_age=case.patient_age,
            patient_gender=case.patient_gender,
            chief_complaint=case.chief_complaint,
        )
        clinical_interp = ClinicalInterpretation(
            analysis_id=analysis.id,
            clinical_summary=interp.get("clinical_summary", ""),
            differential_diagnosis=interp.get("differential_diagnosis", ""),
            recommendations=interp.get("recommendations", ""),
            gemini_raw=str(interp),
        )
        db.add(clinical_interp)
        db.commit()
        db.refresh(clinical_interp)
    except Exception:
        clinical_interp = None

    # Update case status
    case.status = "analyzed"
    db.commit()

    return _to_analysis_response(analysis)


@router.get("/analyses/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(analysis_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return _to_analysis_response(analysis)


@router.get("/cases/{case_id}/analyses", response_model=List[AnalysisResponse])
def list_analyses(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    analyses = db.query(Analysis).filter(Analysis.case_id == case_id).order_by(Analysis.created_at.desc()).all()
    return [_to_analysis_response(a) for a in analyses]


@router.get("/gradcam/{filename}")
def get_gradcam_image(filename: str):
    filepath = os.path.join(settings.GRADCAM_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Grad-CAM image not found")
    return FileResponse(filepath, media_type="image/png")


@router.post("/analyses/{analysis_id}/review", response_model=ReviewResponse, status_code=201)
def submit_review(
    analysis_id: int,
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    existing = db.query(ClinicianReview).filter(ClinicianReview.analysis_id == analysis_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Review already submitted")

    review = ClinicianReview(
        analysis_id=analysis_id,
        reviewer_id=current_user.id,
        agrees_with_ai=data.agrees_with_ai,
        clinician_diagnosis=data.clinician_diagnosis,
        clinical_notes=data.clinical_notes,
        action_taken=data.action_taken,
    )
    db.add(review)

    # Update case status
    case = db.query(PatientCase).filter(PatientCase.id == analysis.case_id).first()
    if case:
        case.status = "reviewed"

    db.commit()
    db.refresh(review)
    return ReviewResponse.model_validate(review)


def _to_analysis_response(analysis: Analysis) -> AnalysisResponse:
    interp = None
    if analysis.interpretation:
        interp = InterpretationResponse.model_validate(analysis.interpretation)
    rev = None
    if analysis.review:
        rev = ReviewResponse.model_validate(analysis.review)

    return AnalysisResponse(
        id=analysis.id,
        image_id=analysis.image_id,
        case_id=analysis.case_id,
        module=analysis.module,
        model_name=analysis.model_name,
        predicted_class=analysis.predicted_class,
        confidence_score=analysis.confidence_score,
        all_predictions=analysis.all_predictions,
        gradcam_path=analysis.gradcam_path,
        processing_time_ms=analysis.processing_time_ms,
        created_at=analysis.created_at,
        interpretation=interp,
        review=rev,
    )
