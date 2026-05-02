import os
import uuid
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import User, PatientCase, MedicalImage, Analysis, ClinicianReview, DiagnosticReport
from app.schemas import CaseCreate, CaseResponse, CaseDetailResponse, ImageResponse, ReportResponse
from app.utils import get_current_user
from app.config import settings
from app.services.gemini_service import generate_diagnostic_report

router = APIRouter(prefix="/api/cases", tags=["Patient Cases"])


@router.post("", response_model=CaseResponse, status_code=201)
def create_case(data: CaseCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    case = PatientCase(
        user_id=current_user.id,
        patient_id=data.patient_id,
        patient_age=data.patient_age,
        patient_gender=data.patient_gender,
        chief_complaint=data.chief_complaint,
        clinical_notes=data.clinical_notes,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return _to_case_response(case, db)


@router.get("", response_model=List[CaseResponse])
def list_cases(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cases = db.query(PatientCase).filter(PatientCase.user_id == current_user.id).order_by(
        PatientCase.created_at.desc()
    ).all()
    return [_to_case_response(c, db) for c in cases]


@router.get("/{case_id}", response_model=CaseDetailResponse)
def get_case(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    case = db.query(PatientCase).filter(PatientCase.id == case_id, PatientCase.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    resp = _to_case_response(case, db)
    images = [ImageResponse.model_validate(img) for img in case.images]
    return CaseDetailResponse(**resp.model_dump(), images=images)


@router.post("/{case_id}/images", response_model=ImageResponse, status_code=201)
def upload_image(
    case_id: int,
    image_type: str = Form(default="chest_xray"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    case = db.query(PatientCase).filter(PatientCase.id == case_id, PatientCase.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    # Save file
    ext = os.path.splitext(file.filename)[1] if file.filename else ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    image = MedicalImage(
        case_id=case_id,
        image_type=image_type,
        file_path=filename,
        original_filename=file.filename or "unknown",
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return ImageResponse.model_validate(image)


@router.get("/{case_id}/images/{image_id}/file")
def get_image_file(case_id: int, image_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    img = db.query(MedicalImage).filter(MedicalImage.id == image_id, MedicalImage.case_id == case_id).first()
    if not img:
        raise HTTPException(status_code=404, detail="Image not found")
    filepath = os.path.join(settings.UPLOAD_DIR, img.file_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(filepath)


@router.post("/{case_id}/report", response_model=ReportResponse, status_code=201)
def create_report(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    case = db.query(PatientCase).filter(PatientCase.id == case_id, PatientCase.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    analyses = db.query(Analysis).filter(Analysis.case_id == case_id).all()
    reviews = db.query(ClinicianReview).join(Analysis).filter(Analysis.case_id == case_id).all()

    analyses_data = [
        {
            "module": a.module,
            "predicted_class": a.predicted_class,
            "confidence": a.confidence_score,
            "all_predictions": a.all_predictions,
            "interpretation": a.interpretation.clinical_summary if a.interpretation else "Pending",
        }
        for a in analyses
    ]
    reviews_data = [
        {
            "agrees_with_ai": r.agrees_with_ai,
            "clinician_diagnosis": r.clinician_diagnosis,
            "clinical_notes": r.clinical_notes,
        }
        for r in reviews
    ]

    content = generate_diagnostic_report(
        case_info={
            "patient_id": case.patient_id,
            "patient_age": case.patient_age,
            "patient_gender": case.patient_gender,
            "chief_complaint": case.chief_complaint,
            "clinical_notes": case.clinical_notes,
        },
        analyses=analyses_data,
        reviews=reviews_data,
        clinician_name=current_user.full_name,
        organization=current_user.organization,
    )

    report = DiagnosticReport(case_id=case_id, content_markdown=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    return ReportResponse.model_validate(report)


@router.get("/{case_id}/reports", response_model=List[ReportResponse])
def list_reports(case_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    case = db.query(PatientCase).filter(PatientCase.id == case_id, PatientCase.user_id == current_user.id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    reports = db.query(DiagnosticReport).filter(DiagnosticReport.case_id == case_id).order_by(
        DiagnosticReport.created_at.desc()
    ).all()
    return [ReportResponse.model_validate(r) for r in reports]


def _to_case_response(case: PatientCase, db: Session) -> CaseResponse:
    img_count = db.query(MedicalImage).filter(MedicalImage.case_id == case.id).count()
    analysis_count = db.query(Analysis).filter(Analysis.case_id == case.id).count()
    return CaseResponse(
        id=case.id,
        user_id=case.user_id,
        patient_id=case.patient_id,
        patient_age=case.patient_age,
        patient_gender=case.patient_gender,
        chief_complaint=case.chief_complaint,
        clinical_notes=case.clinical_notes,
        status=case.status,
        created_at=case.created_at,
        image_count=img_count,
        analysis_count=analysis_count,
    )
