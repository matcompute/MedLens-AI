from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="clinician")  # admin, clinician, radiologist, researcher
    specialty = Column(String(255), default="")
    organization = Column(String(255), default="")
    license_number = Column(String(100), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    cases = relationship("PatientCase", back_populates="clinician")
    reviews = relationship("ClinicianReview", back_populates="reviewer")


class PatientCase(Base):
    __tablename__ = "patient_cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    patient_id = Column(String(100), default="")  # anonymized ID
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String(20), default="")
    chief_complaint = Column(Text, default="")
    clinical_notes = Column(Text, default="")
    status = Column(String(50), default="new")  # new, analyzed, reviewed, closed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    clinician = relationship("User", back_populates="cases")
    images = relationship("MedicalImage", back_populates="case", cascade="all, delete-orphan")
    reports = relationship("DiagnosticReport", back_populates="case", cascade="all, delete-orphan")


class MedicalImage(Base):
    __tablename__ = "medical_images"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("patient_cases.id"), nullable=False)
    image_type = Column(String(50), default="chest_xray")  # chest_xray, skin_lesion, retinal
    file_path = Column(String(500), nullable=False)
    original_filename = Column(String(255), default="")
    upload_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("PatientCase", back_populates="images")
    analyses = relationship("Analysis", back_populates="image", cascade="all, delete-orphan")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    image_id = Column(Integer, ForeignKey("medical_images.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("patient_cases.id"), nullable=False)
    module = Column(String(50), nullable=False)  # chest_xray, skin_lesion, retinal
    model_name = Column(String(100), default="")
    model_version = Column(String(50), default="1.0")
    predicted_class = Column(String(100), nullable=False)
    confidence_score = Column(Float, nullable=False)
    all_predictions = Column(JSON, default=dict)  # {class: probability}
    gradcam_path = Column(String(500), default="")
    processing_time_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    image = relationship("MedicalImage", back_populates="analyses")
    interpretation = relationship("ClinicalInterpretation", back_populates="analysis", uselist=False, cascade="all, delete-orphan")
    review = relationship("ClinicianReview", back_populates="analysis", uselist=False, cascade="all, delete-orphan")


class ClinicalInterpretation(Base):
    __tablename__ = "clinical_interpretations"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    clinical_summary = Column(Text, default="")
    differential_diagnosis = Column(Text, default="")
    recommendations = Column(Text, default="")
    gemini_raw = Column(Text, default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("Analysis", back_populates="interpretation")


class ClinicianReview(Base):
    __tablename__ = "clinician_reviews"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agrees_with_ai = Column(Boolean, default=True)
    clinician_diagnosis = Column(String(255), default="")
    clinical_notes = Column(Text, default="")
    action_taken = Column(String(100), default="")  # confirm, override, refer, order_tests
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    analysis = relationship("Analysis", back_populates="review")
    reviewer = relationship("User", back_populates="reviews")


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("patient_cases.id"), nullable=False)
    content_markdown = Column(Text, default="")
    generated_by = Column(String(50), default="gemini")
    review_status = Column(String(50), default="draft")  # draft, reviewed, approved
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    case = relationship("PatientCase", back_populates="reports")
