import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';

interface Case {
  id: number; patient_id: string; patient_age: number | null; patient_gender: string;
  chief_complaint: string; status: string; created_at: string; image_count: number; analysis_count: number;
}

export default function CasesPage() {
  const [cases, setCases] = useState<Case[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ patient_id: '', patient_age: '', patient_gender: '', chief_complaint: '', clinical_notes: '' });
  const navigate = useNavigate();

  useEffect(() => { loadCases(); }, []);

  const loadCases = () => api.get('/cases').then(r => setCases(r.data));

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    await api.post('/cases', { ...form, patient_age: form.patient_age ? parseInt(form.patient_age) : null });
    setShowCreate(false);
    setForm({ patient_id: '', patient_age: '', patient_gender: '', chief_complaint: '', clinical_notes: '' });
    loadCases();
  };

  const statusBadge = (s: string) => {
    const map: Record<string, string> = { new: 'badge-gray', analyzed: 'badge-teal', reviewed: 'badge-green', closed: 'badge-blue' };
    return <span className={`badge ${map[s] || 'badge-gray'}`}>{s}</span>;
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: 700, marginBottom: '8px' }}>Patient Cases</h1>
          <p style={{ color: 'var(--text-secondary)' }}>Manage diagnostic cases and imaging studies</p>
        </div>
        <button className="btn btn-primary" onClick={() => setShowCreate(true)}>+ New Case</button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 className="card-title" style={{ marginBottom: '16px' }}>Create Patient Case</h3>
          <form onSubmit={handleCreate}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label>Patient ID</label>
                <input value={form.patient_id} onChange={e => setForm({ ...form, patient_id: e.target.value })} placeholder="PT-001" />
              </div>
              <div className="form-group">
                <label>Age</label>
                <input type="number" value={form.patient_age} onChange={e => setForm({ ...form, patient_age: e.target.value })} placeholder="45" />
              </div>
              <div className="form-group">
                <label>Gender</label>
                <select value={form.patient_gender} onChange={e => setForm({ ...form, patient_gender: e.target.value })}>
                  <option value="">Select</option>
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>Chief Complaint</label>
              <input value={form.chief_complaint} onChange={e => setForm({ ...form, chief_complaint: e.target.value })} placeholder="Persistent cough, fever for 3 days" />
            </div>
            <div className="form-group">
              <label>Clinical Notes</label>
              <textarea rows={3} value={form.clinical_notes} onChange={e => setForm({ ...form, clinical_notes: e.target.value })} placeholder="Additional clinical observations..." />
            </div>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
              <button type="submit" className="btn btn-primary">Create Case</button>
            </div>
          </form>
        </div>
      )}

      <div className="card">
        {cases.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📁</div>
            <p>No cases yet. Create one or use Analyze Image for quick analysis.</p>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Patient ID</th>
                  <th>Age/Gender</th>
                  <th>Chief Complaint</th>
                  <th>Images</th>
                  <th>Analyses</th>
                  <th>Status</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {cases.map(c => (
                  <tr key={c.id}>
                    <td><strong>{c.patient_id || `Case #${c.id}`}</strong></td>
                    <td>{c.patient_age || '—'} / {c.patient_gender || '—'}</td>
                    <td style={{ maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {c.chief_complaint || '—'}
                    </td>
                    <td>{c.image_count}</td>
                    <td>{c.analysis_count}</td>
                    <td>{statusBadge(c.status)}</td>
                    <td>{new Date(c.created_at).toLocaleDateString()}</td>
                    <td>
                      <button className="btn btn-sm btn-secondary" onClick={() => navigate(`/cases/${c.id}`)}>View</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
