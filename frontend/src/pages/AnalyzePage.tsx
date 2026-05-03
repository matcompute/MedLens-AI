import { useState, useRef } from 'react';
import api from '../api/client';

interface AnalysisResult {
  id: number; predicted_class: string; confidence_score: number; module: string;
  model_name: string; all_predictions: Record<string, number>; gradcam_path: string;
  processing_time_ms: number;
  interpretation?: { clinical_summary: string; differential_diagnosis: string; recommendations: string };
}

export default function AnalyzePage() {
  const [step, setStep] = useState<'upload' | 'analyzing' | 'results'>('upload');
  const [imageType, setImageType] = useState('chest_xray');
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState('');
  const [caseId, setCaseId] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Patient info
  const [patientId, setPatientId] = useState('');
  const [patientAge, setPatientAge] = useState('');
  const [patientGender, setPatientGender] = useState('');
  const [chiefComplaint, setChiefComplaint] = useState('');
  const [clinicalNotes, setClinicalNotes] = useState('');

  const moduleInfo: Record<string, { label: string; icon: string; desc: string }> = {
    chest_xray: { label: 'Chest X-Ray', icon: '\u{1FAC1}', desc: 'Pneumonia, Cardiomegaly, Pleural Effusion' },
    skin_lesion: { label: 'Skin Lesion', icon: '\u{1F50D}', desc: 'Melanoma, BCC, Benign Keratosis' },
    retinal: { label: 'Retinal Scan', icon: '\u{1F441}', desc: 'Diabetic Retinopathy grading' },
  };

  const handleFile = (f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setError('');
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files[0];
    if (f && f.type.startsWith('image/')) handleFile(f);
  };

  const handleAnalyze = async () => {
    if (!file) return;
    setStep('analyzing'); setError('');

    try {
      // Create case with patient info
      const caseRes = await api.post('/cases', {
        patient_id: patientId || `PT-${Date.now().toString(36).toUpperCase()}`,
        patient_age: patientAge ? parseInt(patientAge) : null,
        patient_gender: patientGender || null,
        chief_complaint: chiefComplaint || `${moduleInfo[imageType].label} analysis`,
        clinical_notes: clinicalNotes || null,
      });
      const cId = caseRes.data.id;
      setCaseId(cId);

      // Upload image
      const formData = new FormData();
      formData.append('file', file);
      formData.append('image_type', imageType);
      const imgRes = await api.post(`/cases/${cId}/images`, formData);

      // Run analysis
      const analysisRes = await api.post(`/analyze/${imgRes.data.id}`);
      setResult(analysisRes.data);
      setStep('results');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
      setStep('upload');
    }
  };

  const handleReset = () => {
    setStep('upload'); setFile(null); setPreview(''); setResult(null); setError('');
    setPatientId(''); setPatientAge(''); setPatientGender('');
    setChiefComplaint(''); setClinicalNotes('');
  };

  return (
    <div>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>Analyze Image</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>
        Upload a medical image for AI-powered diagnostic screening
      </p>

      {step === 'upload' && (
        <>
          {/* Module selector */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginBottom: '24px' }}>
            {Object.entries(moduleInfo).map(([key, info]) => (
              <div key={key} className="card" onClick={() => setImageType(key)}
                style={{
                  cursor: 'pointer', textAlign: 'center',
                  borderColor: imageType === key ? 'var(--accent)' : undefined,
                  background: imageType === key ? 'var(--accent-glow)' : undefined,
                }}>
                <div style={{ fontSize: '36px', marginBottom: '8px' }}>{info.icon}</div>
                <div style={{ fontWeight: 600, marginBottom: '4px' }}>{info.label}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{info.desc}</div>
              </div>
            ))}
          </div>

          {/* Patient Information */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <h3 className="card-title" style={{ marginBottom: '16px' }}>Patient Information</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label>Patient ID</label>
                <input value={patientId} onChange={e => setPatientId(e.target.value)}
                  placeholder="PT-001 (auto-generated if empty)" />
              </div>
              <div className="form-group">
                <label>Age</label>
                <input type="number" value={patientAge} onChange={e => setPatientAge(e.target.value)}
                  placeholder="e.g. 45" />
              </div>
              <div className="form-group">
                <label>Gender</label>
                <select value={patientGender} onChange={e => setPatientGender(e.target.value)}>
                  <option value="">Select gender</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Chief Complaint</label>
              <input value={chiefComplaint} onChange={e => setChiefComplaint(e.target.value)}
                placeholder="e.g. Persistent cough, shortness of breath for 5 days" />
            </div>
            <div className="form-group">
              <label>Clinical Notes (optional)</label>
              <textarea rows={2} value={clinicalNotes} onChange={e => setClinicalNotes(e.target.value)}
                placeholder="Additional observations, history, medications..." />
            </div>
          </div>

          {/* Upload zone */}
          <div className={`upload-zone`}
            onDrop={handleDrop} onDragOver={e => e.preventDefault()}
            onClick={() => fileRef.current?.click()}>
            <input ref={fileRef} type="file" accept="image/*" hidden onChange={e => {
              const f = e.target.files?.[0];
              if (f) handleFile(f);
            }} />
            {preview ? (
              <div>
                <img src={preview} alt="Preview" style={{ maxWidth: '300px', maxHeight: '300px', borderRadius: '8px', marginBottom: '16px' }} />
                <div style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>{file?.name}</div>
              </div>
            ) : (
              <div>
                <div className="upload-icon">📤</div>
                <div className="upload-text">Drop a medical image here or click to browse</div>
                <div className="upload-hint">Supports JPEG, PNG — Max 10MB</div>
              </div>
            )}
          </div>

          {error && <p style={{ color: '#ef4444', marginTop: '12px' }}>{error}</p>}

          <div style={{ marginTop: '20px', display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            {file && <button className="btn btn-secondary" onClick={handleReset}>Clear</button>}
            <button className="btn btn-primary" disabled={!file} onClick={handleAnalyze}>
              🔬 Run AI Analysis
            </button>
          </div>
        </>
      )}

      {step === 'analyzing' && (
        <div className="card" style={{ textAlign: 'center', padding: '60px' }}>
          <div className="spinner" />
          <div className="loading-text" style={{ marginTop: '20px' }}>
            <strong>Running AI Analysis Pipeline...</strong>
            <br /><br />
            1. CNN Classification ({moduleInfo[imageType].label})<br />
            2. Grad-CAM Visual Explanation<br />
            3. Gemini Clinical Interpretation
          </div>
        </div>
      )}

      {step === 'results' && result && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '20px' }}>Analysis Results</h2>
            <button className="btn btn-primary" onClick={handleReset}>+ New Analysis</button>
          </div>

          {/* Primary finding */}
          <div className="card" style={{ marginBottom: '24px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ fontSize: '48px' }}>{moduleInfo[result.module]?.icon}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                  Primary Finding
                </div>
                <div style={{ fontSize: '28px', fontWeight: 700, color: 'var(--accent-text)' }}>
                  {result.predicted_class}
                </div>
                <div style={{ color: 'var(--text-secondary)', fontSize: '14px', marginTop: '4px' }}>
                  Model: {result.model_name} | Processing: {result.processing_time_ms}ms
                  {patientId && <> | Patient: {patientId}</>}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '36px', fontWeight: 800, color: 'var(--accent)' }}>
                  {(result.confidence_score * 100).toFixed(1)}%
                </div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Confidence</div>
              </div>
            </div>
          </div>

          {/* Images side by side */}
          <div className="analysis-grid">
            <div className="image-viewer">
              <div className="image-viewer-label">Original Image</div>
              <img src={preview} alt="Original" />
            </div>
            {result.gradcam_path && (
              <div className="image-viewer">
                <div className="image-viewer-label">Grad-CAM Heatmap</div>
                <img src={`/api/gradcam/${result.gradcam_path}`} alt="Grad-CAM" />
              </div>
            )}
          </div>

          {/* Confidence bars */}
          <div className="card" style={{ marginTop: '24px' }}>
            <h3 className="card-title" style={{ marginBottom: '16px' }}>All Predictions</h3>
            {Object.entries(result.all_predictions)
              .sort(([, a], [, b]) => b - a)
              .map(([cls, prob]) => (
                <div key={cls} className="confidence-bar">
                  <span className="label">{cls}</span>
                  <div className="bar-bg">
                    <div className="bar-fill" style={{
                      width: `${prob * 100}%`,
                      background: cls === result.predicted_class
                        ? 'linear-gradient(90deg, var(--accent), #0891b2)'
                        : 'var(--text-muted)',
                    }} />
                  </div>
                  <span className="value">{(prob * 100).toFixed(1)}%</span>
                </div>
              ))}
          </div>

          {/* Gemini interpretation */}
          {result.interpretation && (
            <div className="interpretation-card" style={{ marginTop: '24px' }}>
              <h3>Clinical Interpretation (Gemini AI)</h3>
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ color: 'var(--text-primary)', fontSize: '14px', marginBottom: '8px' }}>Summary</h4>
                <p>{result.interpretation.clinical_summary}</p>
              </div>
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ color: 'var(--text-primary)', fontSize: '14px', marginBottom: '8px' }}>Differential Diagnosis</h4>
                <p>{result.interpretation.differential_diagnosis}</p>
              </div>
              <div>
                <h4 style={{ color: 'var(--text-primary)', fontSize: '14px', marginBottom: '8px' }}>Recommendations</h4>
                <p>{result.interpretation.recommendations}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
