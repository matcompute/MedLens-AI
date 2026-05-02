# MedLens AI

**AI-Powered Medical Image Diagnostics Platform**

MedLens AI is a full-stack clinical decision support system that uses deep learning (CNN) and Google Gemini to assist healthcare professionals with diagnostic imaging. Upload a medical image, get an instant AI classification, see Grad-CAM visual explanations showing where the AI is looking, and receive a Gemini-powered clinical interpretation.

> This is a research and screening triage tool, not a certified medical device. Clinicians make the final diagnosis.

---

## Features

| Feature | Description |
|---|---|
| **CNN Image Classification** | DenseNet121 (Chest X-Ray), EfficientNet-B0 (Skin Lesion), ResNet50 (Retinal Scan) |
| **Grad-CAM Heatmaps** | Visual explanations highlighting diagnostic regions of interest |
| **Gemini Clinical Interpretation** | AI-generated clinical summary, differential diagnosis, and next-step recommendations |
| **Patient Case Management** | Create cases, upload images, track analysis history |
| **Clinician Review Workflow** | Agree/Override AI findings with clinical notes (EU AI Act Art. 14 human oversight) |
| **Diagnostic Reports** | Gemini-generated full diagnostic reports per patient case |
| **JWT Authentication** | Secure clinician accounts with role and specialty tracking |

---

## Architecture

```
Frontend (React 18 + TypeScript + Vite)
    |
    | REST API + Image Upload
    |
Backend (FastAPI + Python)
    |
    ├── PyTorch CNNs (DenseNet121, EfficientNet-B0, ResNet50)
    ├── Grad-CAM (pytorch-grad-cam)
    ├── Google Gemini API (clinical interpretation)
    └── SQLite / PostgreSQL
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10, FastAPI, SQLAlchemy, Pydantic v2 |
| Frontend | React 18, TypeScript, Vite 5 |
| ML / Computer Vision | PyTorch, torchvision (ResNet50, DenseNet121, EfficientNet-B0) |
| Explainability (XAI) | pytorch-grad-cam (Grad-CAM, Grad-CAM++, EigenCAM) |
| LLM | Google Gemini API (clinical interpretation, report generation) |
| Auth | JWT + bcrypt |
| Database | SQLite (dev), PostgreSQL-ready |

---

## Diagnostic Modules

### Chest X-Ray Analysis
- **Model**: DenseNet121
- **Classes**: Normal, Pneumonia, Cardiomegaly, Pleural Effusion, Atelectasis

### Skin Lesion Classification
- **Model**: EfficientNet-B0
- **Classes**: Melanoma, Basal Cell Carcinoma, Benign Keratosis, Dermatofibroma, Melanocytic Nevus

### Retinal Scan Analysis
- **Model**: ResNet50
- **Classes**: Normal, Mild DR, Moderate DR, Severe DR, Proliferative DR

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- Google Gemini API key

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
```

For PyTorch CPU:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
pip install grad-cam
```

### Frontend Setup

```bash
cd frontend
npm install
```

### Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.5-flash
```

### Run

```bash
# Terminal 1 - Backend (port 8000)
cd backend
venv\Scripts\python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend (port 5173)
cd frontend
npx vite --port 5173
```

Open **http://localhost:5173**

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register clinician account |
| POST | `/api/auth/login` | Authenticate |
| GET | `/api/auth/me` | Current user profile |
| GET | `/api/dashboard/summary` | Dashboard statistics |
| POST | `/api/cases` | Create patient case |
| GET | `/api/cases` | List cases |
| GET | `/api/cases/{id}` | Case detail with images |
| POST | `/api/cases/{id}/images` | Upload medical image |
| POST | `/api/analyze/{image_id}` | Run AI analysis (CNN + Grad-CAM + Gemini) |
| GET | `/api/analyses/{id}` | Get analysis results |
| GET | `/api/gradcam/{filename}` | Serve Grad-CAM heatmap |
| POST | `/api/analyses/{id}/review` | Submit clinician review |
| POST | `/api/cases/{id}/report` | Generate diagnostic report |

---

## Database Schema

| Table | Purpose |
|---|---|
| `users` | Clinician accounts (email, name, specialty, organization) |
| `patient_cases` | Patient case records with clinical notes |
| `medical_images` | Uploaded imaging files |
| `analyses` | CNN classification results + Grad-CAM paths |
| `clinical_interpretations` | Gemini-generated clinical summaries |
| `clinician_reviews` | Human oversight decisions (agree/override) |
| `diagnostic_reports` | Full Gemini-generated diagnostic reports |

---

## How It Works

1. **Register** as a clinician with your specialty and organization
2. **Create a patient case** or use quick analysis mode
3. **Upload a medical image** and select the diagnostic module
4. **AI Pipeline runs automatically**:
   - CNN classifies the image (DenseNet121 / EfficientNet-B0 / ResNet50)
   - Grad-CAM generates a heatmap showing diagnostic regions
   - Gemini provides clinical interpretation with differential diagnosis
5. **Clinician reviews**: Agree with AI or override with your own diagnosis
6. **Generate a report**: Full diagnostic summary via Gemini

---

## Regulatory Context

MedLens AI is designed with awareness of:

- **EU AI Act** (Regulation 2024/1689) — High-risk AI system requirements
- **EU MDR** (2017/745) — Medical Device Regulation for diagnostic software
- **Article 14** — Human oversight provisions (clinician review workflow)
- **Article 13** — Transparency (Grad-CAM explainability)

---

## Project Structure

```
MedLens/
├── .env                          # API keys (not committed)
├── .env.example                  # Template
├── .gitignore
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── uploads/                  # Uploaded images
│   ├── gradcam_outputs/          # Generated heatmaps
│   └── app/
│       ├── main.py               # FastAPI entry point
│       ├── config.py             # Settings
│       ├── database.py           # SQLAlchemy setup
│       ├── models/__init__.py    # 7 database models
│       ├── schemas/__init__.py   # Pydantic schemas
│       ├── routers/
│       │   ├── auth.py           # JWT authentication
│       │   ├── dashboard.py      # Statistics
│       │   ├── cases.py          # Patient cases + images + reports
│       │   └── analysis.py       # CNN + Grad-CAM + Gemini pipeline
│       ├── services/
│       │   ├── ml_service.py     # PyTorch model loading + inference
│       │   ├── gradcam_service.py # Grad-CAM heatmap generation
│       │   └── gemini_service.py  # Clinical interpretation + reports
│       └── utils/__init__.py     # JWT + bcrypt
└── frontend/
    ├── package.json
    ├── vite.config.ts
    └── src/
        ├── App.tsx               # Router
        ├── index.css             # Medical teal design system
        ├── api/client.ts         # Axios + JWT interceptor
        ├── contexts/AuthContext.tsx
        ├── components/Layout.tsx
        └── pages/
            ├── LoginPage.tsx
            ├── DashboardPage.tsx
            ├── AnalyzePage.tsx    # Image upload + instant AI results
            ├── CasesPage.tsx
            └── CaseDetailPage.tsx
```

---

## License

MIT
