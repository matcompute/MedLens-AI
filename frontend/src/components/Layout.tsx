import { NavLink, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">M</div>
          <div>
            <h1>MedLens</h1>
            <span>AI Diagnostics</span>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Main</div>
          <NavLink to="/dashboard" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <span className="icon">📊</span> Dashboard
          </NavLink>
          <NavLink to="/analyze" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <span className="icon">🔬</span> Analyze Image
          </NavLink>
          <NavLink to="/cases" className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}>
            <span className="icon">📁</span> Patient Cases
          </NavLink>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">Modules</div>
          <div className="sidebar-link" style={{ cursor: 'default' }}>
            <span className="icon">🫁</span> Chest X-Ray
          </div>
          <div className="sidebar-link" style={{ cursor: 'default' }}>
            <span className="icon">🔍</span> Skin Lesion
          </div>
          <div className="sidebar-link" style={{ cursor: 'default' }}>
            <span className="icon">👁</span> Retinal Scan
          </div>
        </div>

        <div style={{ flex: 1 }} />
        <div className="sidebar-section">
          <div className="sidebar-section-label">Account</div>
          <div className="sidebar-link" style={{ fontSize: '13px' }}>
            <span className="icon">👤</span> {user?.full_name}
          </div>
          <a onClick={logout} className="sidebar-link" style={{ cursor: 'pointer' }}>
            <span className="icon">🚪</span> Sign Out
          </a>
        </div>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}
