import { useEffect, useState, useRef } from 'react';
import { useParams } from 'react-router-dom';
import api from '../api/client';

export default function CaseDetailPage() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState<any>(null);
  const [analyses, setAnalyses] = useState<any[]>([]);
  const [reports, setReports] = useState<any[]>([]);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [imageType, setImageType] = useState('chest_xray');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { load(); }, [id]);

  const load = async () => {
    const [c, a, r] = await Promise.all([
      api.get(`/cases/${id}`), api.get(`/cases/${id}/analyses`), api.get(`/cases/${id}/reports`),
    ]);
    setCaseData(c.data); setAnalyses(a.data); setReports(r.data);
  };

  const handleUploadAndAnalyze = async (file: File) => {
    setUploading(true); setAnalyzing(true);
    try {
      const fd = new FormData();
      fd.append('file', file); fd.append('image_type', imageType);
      const imgRes = await api.post(`/cases/${id}/images`, fd);
      setUploading(false);
      await api.post(`/analyze/${imgRes.data.id}`);
      await load();
    } catch (err) { console.error(err); }
    setAnalyzing(false); setUploading(false);
  };

  const handleReport = async () => {
    setGeneratingReport(true);
    try { await api.post(`/cases/${id}/report`); await load(); } catch (err) { console.error(err); }
    setGeneratingReport(false);
  };

  const handleReview = async (analysisId: number, agrees: boolean) => {
    await api.post(`/analyses/${analysisId}/review`, {
      agrees_with_ai: agrees, clinician_diagnosis: agrees ? '' : 'Manual review needed',
      clinical_notes: agrees ? 'AI finding confirmed' : 'Clinician disagrees with AI classification',
      action_taken: agrees ? 'confirm' : 'override',
    });
    await load();
  };

  if (!caseData) return <div className="spinner" />;

  const statusBadge = (s: string) => {
    const map: Record<string, string> = { new: 'badge-gray', analyzed: 'badge-teal', reviewed: 'badge-green' };
    return <span className={`badge ${map[s] || 'badge-gray'}`}>{s}</span>;
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: 700 }}>
            Case: {caseData.patient_id || `#${caseData.id}`} {statusBadge(caseData.status)}
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
            {caseData.patient_age && `${caseData.patient_age}y`} {caseData.patient_gender} — {caseData.chief_complaint}
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn btn-primary" onClick={handleReport} disabled={generatingReport}>
            {generatingReport ? 'Generating...' : '📄 Generate Report'}
          </button>
        </div>
      </div>

      {/* Upload + Analyze */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 className="card-title" style={{ marginBottom: '16px' }}>Upload and Analyze</h3>
        <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
          <select value={imageType} onChange={e => setImageType(e.target.value)}
            style={{ padding: '10px 14px', background: 'var(--bg-input)', border: '1px solid var(--border)', borderRadius: '8px', color: 'var(--text-primary)', fontFamily: 'Inter' }}>
            <option value="chest_xray">🫁 Chest X-Ray</option>
            <option value="skin_lesion">🔍 Skin Lesion</option>
            <option value="retinal">👁 Retinal Scan</option>
          </select>
          <input ref={fileRef} type="file" accept="image/*" hidden onChange={e => {
            const f = e.target.files?.[0];
            if (f) handleUploadAndAnalyze(f);
          }} />
          <button className="btn btn-primary" onClick={() => fileRef.current?.click()} disabled={analyzing}>
            {analyzing ? (uploading ? 'Uploading...' : 'Analyzing...') : '📤 Upload and Analyze'}
          </button>
        </div>
      </div>

      {/* Analyses */}
      {analyses.map(a => (
        <div key={a.id} className="card" style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                {a.module.replace('_', ' ')} — {a.model_name}
              </div>
              <div style={{ fontSize: '24px', fontWeight: 700, color: 'var(--accent-text)', marginTop: '4px' }}>
                {a.predicted_class}
                <span style={{ fontSize: '16px', color: 'var(--text-secondary)', marginLeft: '12px' }}>
                  {(a.confidence_score * 100).toFixed(1)}% confidence
                </span>
              </div>
            </div>
            {!a.review && (
              <div style={{ display: 'flex', gap: '8px' }}>
                <button className="btn btn-sm btn-primary" onClick={() => handleReview(a.id, true)}>✓ Agree</button>
                <button className="btn btn-sm btn-danger" onClick={() => handleReview(a.id, false)}>✗ Override</button>
              </div>
            )}
            {a.review && (
              <span className={`badge ${a.review.agrees_with_ai ? 'badge-green' : 'badge-red'}`}>
                {a.review.agrees_with_ai ? 'Confirmed' : 'Overridden'}
              </span>
            )}
          </div>

          {/* Images */}
          <div className="analysis-grid" style={{ marginTop: '16px' }}>
            <div className="image-viewer">
              <div className="image-viewer-label">Original</div>
              <img src={`/api/cases/${id}/images/${a.image_id}/file`} alt="Original" />
            </div>
            {a.gradcam_path && (
              <div className="image-viewer">
                <div className="image-viewer-label">Grad-CAM Heatmap</div>
                <img src={`/api/gradcam/${a.gradcam_path}`} alt="Grad-CAM" />
              </div>
            )}
          </div>

          {/* Predictions */}
          <div style={{ marginTop: '16px' }}>
            {Object.entries(a.all_predictions as Record<string, number>)
              .sort(([, x], [, y]) => (y as number) - (x as number))
              .map(([cls, prob]) => (
                <div key={cls} className="confidence-bar">
                  <span className="label">{cls}</span>
                  <div className="bar-bg">
                    <div className="bar-fill" style={{
                      width: `${(prob as number) * 100}%`,
                      background: cls === a.predicted_class ? 'linear-gradient(90deg, var(--accent), #0891b2)' : 'var(--text-muted)',
                    }} />
                  </div>
                  <span className="value">{((prob as number) * 100).toFixed(1)}%</span>
                </div>
              ))}
          </div>

          {/* Interpretation */}
          {a.interpretation && (
            <div className="interpretation-card">
              <h3>Clinical Interpretation</h3>
              <p>{a.interpretation.clinical_summary}</p>
              <h4 style={{ color: 'var(--text-primary)', fontSize: '14px', marginTop: '12px' }}>Differential Diagnosis</h4>
              <p>{a.interpretation.differential_diagnosis}</p>
              <h4 style={{ color: 'var(--text-primary)', fontSize: '14px', marginTop: '12px' }}>Recommendations</h4>
              <p>{a.interpretation.recommendations}</p>
            </div>
          )}
        </div>
      ))}

      {analyses.length === 0 && (
        <div className="card"><div className="empty-state"><div className="empty-icon">🔬</div><p>No analyses yet. Upload an image above.</p></div></div>
      )}

      {/* Reports */}
      {reports.length > 0 && (
        <div className="card" style={{ marginTop: '24px' }}>
          <h3 className="card-title" style={{ marginBottom: '16px' }}>Diagnostic Reports</h3>
          {reports.map(r => (
            <div key={r.id} style={{ padding: '16px', background: 'var(--bg-primary)', borderRadius: '8px', marginBottom: '12px' }}>
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                {new Date(r.created_at).toLocaleString()} — {r.review_status}
              </div>
              <div className="markdown-content" dangerouslySetInnerHTML={{ __html: simpleMarkdown(r.content_markdown) }} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function simpleMarkdown(md: string): string {
  return md
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*$)/gm, '<li>$1</li>')
    .replace(/^---$/gm, '<hr/>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br/>');
}
