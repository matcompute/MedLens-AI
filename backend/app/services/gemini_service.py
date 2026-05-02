"""
MedLens Gemini Service — Clinical interpretation and diagnostic reports.

Uses Google Gemini to provide clinical context for AI predictions,
differential diagnoses, and full diagnostic reports.
"""

import json
from datetime import datetime, timezone
from typing import Dict, Any
from google import genai
from app.config import settings


def _get_client():
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def _generate(prompt: str) -> str:
    client = _get_client()
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
    )
    return response.text or ""


def interpret_analysis(
    module: str,
    predicted_class: str,
    confidence: float,
    all_predictions: Dict[str, float],
    patient_age: int = None,
    patient_gender: str = "",
    chief_complaint: str = "",
) -> Dict[str, str]:
    """
    Use Gemini to provide clinical interpretation of AI classification results.

    Returns dict with: clinical_summary, differential_diagnosis, recommendations
    """
    module_names = {
        "chest_xray": "Chest X-Ray",
        "skin_lesion": "Dermatological Lesion",
        "retinal": "Retinal Fundoscopy",
    }
    exam_type = module_names.get(module, module)

    patient_info = ""
    if patient_age:
        patient_info += f"Age: {patient_age}. "
    if patient_gender:
        patient_info += f"Gender: {patient_gender}. "
    if chief_complaint:
        patient_info += f"Chief complaint: {chief_complaint}. "

    prompt = f"""You are a senior radiologist and diagnostician providing clinical decision support.
An AI screening system has analyzed a {exam_type} image and produced the following classification results.

Provide your clinical interpretation as a JSON object with these exact keys (no markdown, no code fences):
{{
    "clinical_summary": "2-3 paragraph clinical interpretation of the AI findings in professional medical language. Reference the confidence scores and what the finding means clinically.",
    "differential_diagnosis": "List of 3-5 differential diagnoses to consider, ordered by likelihood, with brief clinical reasoning for each.",
    "recommendations": "Specific next steps: additional imaging, lab tests, specialist referral, or follow-up timeline."
}}

AI Classification Results:
- Examination Type: {exam_type}
- Primary Finding: {predicted_class} (Confidence: {confidence:.1%})
- All Class Probabilities: {json.dumps(all_predictions, indent=2)}

Patient Context: {patient_info if patient_info else "No patient information provided."}

IMPORTANT:
- This is a decision SUPPORT tool. Always emphasize that clinical correlation is required.
- Be thorough but concise. Use proper medical terminology.
- Include confidence level assessment (high confidence vs borderline)."""

    try:
        text = _generate(prompt)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1]
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    except (json.JSONDecodeError, Exception) as e:
        return {
            "clinical_summary": f"AI analysis detected {predicted_class} with {confidence:.1%} confidence. Clinical correlation recommended. Automated interpretation unavailable: {str(e)[:100]}",
            "differential_diagnosis": "Automated differential unavailable. Please consult with specialist.",
            "recommendations": "Manual clinical review recommended. Consider repeat imaging if findings are inconclusive.",
        }


def generate_diagnostic_report(
    case_info: Dict[str, Any],
    analyses: list,
    reviews: list,
    clinician_name: str = "",
    organization: str = "",
) -> str:
    """Generate a full diagnostic report for a patient case using Gemini."""

    today = datetime.now(timezone.utc).strftime("%B %d, %Y")
    preparer = clinician_name or "MedLens AI Diagnostic Engine"
    org = organization or "Healthcare Organization"

    analyses_text = ""
    for a in analyses:
        analyses_text += f"""
- Image Type: {a.get('module', 'Unknown')}
- AI Classification: {a.get('predicted_class', 'N/A')} (Confidence: {a.get('confidence', 0):.1%})
- Predictions: {json.dumps(a.get('all_predictions', {}), indent=2)}
- Clinical Interpretation: {a.get('interpretation', 'Pending')}
"""

    reviews_text = ""
    for r in reviews:
        status = "Agrees" if r.get("agrees_with_ai") else "Disagrees"
        reviews_text += f"- Clinician {status} with AI. Diagnosis: {r.get('clinician_diagnosis', 'N/A')}. Notes: {r.get('clinical_notes', 'N/A')}\n"

    prompt = f"""You are a senior medical report writer. Generate a comprehensive diagnostic report in professional Markdown format.

IMPORTANT: Use today's date: {today}. Do NOT use any other date.

Document Header:
- Report Title: MedLens AI Diagnostic Report
- Date: {today}
- Patient ID: {case_info.get('patient_id', 'Anonymous')}
- Patient Age: {case_info.get('patient_age', 'N/A')}
- Patient Gender: {case_info.get('patient_gender', 'N/A')}
- Chief Complaint: {case_info.get('chief_complaint', 'N/A')}
- Prepared by: {preparer}
- Organization: {org}
- Generated via: MedLens AI Diagnostic Platform

Clinical Notes: {case_info.get('clinical_notes', 'None provided')}

AI Analysis Results:
{analyses_text if analyses_text else "No AI analyses performed yet."}

Clinician Reviews:
{reviews_text if reviews_text else "No clinician reviews recorded yet."}

Generate sections:
1. Patient Information
2. Clinical Presentation
3. AI-Assisted Findings (for each analyzed image)
4. Clinician Review Summary
5. Differential Diagnosis
6. Recommendations and Next Steps
7. Disclaimer (this is AI-assisted, not a final diagnosis)

Be thorough, professional, and clinically accurate. Do NOT use placeholder brackets."""

    try:
        return _generate(prompt)
    except Exception as e:
        return f"# Diagnostic Report Generation Error\n\nUnable to generate report: {str(e)}\n\nPlease retry."
