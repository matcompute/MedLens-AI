import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import api from '../api/client';

interface User {
  id: number; email: string; full_name: string; role: string;
  specialty: string; organization: string;
}

interface AuthCtx {
  user: User | null; token: string | null; loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: any) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthCtx>({} as AuthCtx);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('medlens_token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      api.get('/auth/me').then(r => setUser(r.data)).catch(() => {
        localStorage.removeItem('medlens_token'); setToken(null);
      }).finally(() => setLoading(false));
    } else { setLoading(false); }
  }, [token]);

  const login = async (email: string, password: string) => {
    const r = await api.post('/auth/login', { email, password });
    localStorage.setItem('medlens_token', r.data.access_token);
    setToken(r.data.access_token); setUser(r.data.user);
  };

  const register = async (data: any) => {
    const r = await api.post('/auth/register', data);
    localStorage.setItem('medlens_token', r.data.access_token);
    setToken(r.data.access_token); setUser(r.data.user);
  };

  const logout = () => {
    localStorage.removeItem('medlens_token');
    setToken(null); setUser(null);
  };

  return <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
    {children}
  </AuthContext.Provider>;
}
