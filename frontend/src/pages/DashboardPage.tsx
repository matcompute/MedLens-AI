import { useEffect, useState } from 'react';
import api from '../api/client';

interface Summary {
  total_cases: number; total_analyses: number; pending_reviews: number;
  ai_agreement_rate: number;
  cases_by_module: Record<string, number>;
  recent_analyses: Array<{ id: number; module: string; predicted_class: string; confidence: number; created_at: string }>;
}

export default function DashboardPage() {
  const [data, setData] = useState<Summary | null>(null);

  useEffect(() => {
    api.get('/dashboard/summary').then(r => setData(r.data));
  }, []);

  if (!data) return <div className="spinner" />;

  const moduleLabels: Record<string, string> = {
    chest_xray: 'Chest X-Ray', skin_lesion: 'Skin Lesion', retinal: 'Retinal Scan',
  };
  const moduleIcons: Record<string, string> = {
    chest_xray: '🫁', skin_lesion: '🔍', retinal: '👁',
  };

  return (
    <div>
      <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>Dashboard</h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '32px' }}>AI-assisted diagnostic overview</p>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon teal">📁</div>
          <div>
            <div className="stat-value">{data.total_cases}</div>
            <div className="stat-label">Patient Cases</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon blue">🔬</div>
          <div>
            <div className="stat-value">{data.total_analyses}</div>
            <div className="stat-label">AI Analyses</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon amber">⏳</div>
          <div>
            <div className="stat-value">{data.pending_reviews}</div>
            <div className="stat-label">Pending Reviews</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon green">✓</div>
          <div>
            <div className="stat-value">{data.ai_agreement_rate}%</div>
            <div className="stat-label">AI Agreement Rate</div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        <div className="card">
          <div className="card-header"><h3 className="card-title">Analyses by Module</h3></div>
          {Object.entries(data.cases_by_module).map(([mod, count]) => (
            <div key={mod} style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '16px' }}>
              <span style={{ fontSize: '24px' }}>{moduleIcons[mod] || '📊'}</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '14px', fontWeight: 600 }}>{moduleLabels[mod] || mod}</div>
                <div className="confidence-bar" style={{ marginBottom: 0 }}>
                  <div className="bar-bg" style={{ flex: 1 }}>
                    <div className="bar-fill" style={{ width: `${Math.min(100, (count / Math.max(data.total_analyses, 1)) * 100)}%` }} />
                  </div>
                  <span className="value">{count}</span>
                </div>
              </div>
            </div>
          ))}
          {Object.keys(data.cases_by_module).every(k => data.cases_by_module[k] === 0) && (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>No analyses yet. Upload an image to get started.</p>
          )}
        </div>

        <div className="card">
          <div className="card-header"><h3 className="card-title">Recent Analyses</h3></div>
          {data.recent_analyses.length === 0 ? (
            <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '20px' }}>No recent activity</p>
          ) : (
            data.recent_analyses.map(a => (
              <div key={a.id} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: '1px solid var(--border)' }}>
                <div>
                  <span style={{ marginRight: '8px' }}>{moduleIcons[a.module]}</span>
                  <strong>{a.predicted_class}</strong>
                </div>
                <span className="badge badge-teal">{(a.confidence * 100).toFixed(1)}%</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
