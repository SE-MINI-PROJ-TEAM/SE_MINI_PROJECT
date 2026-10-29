import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { get, post, RESET_EVENT, SESSION_EVENT } from '../api/client.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState('loading');
  const [notice, setNotice] = useState('');
  const userRef = useRef(null); // lets the global event handler know whether anyone was signed in
  userRef.current = user;

  const refresh = useCallback(async () => {
    try {
      const { user: me } = await get('/auth/me');
      setUser(me);
    } catch {
      setUser(null);
    } finally {
      setStatus('ready');
    }
  }, []);

  useEffect(() => {
    refresh();
    const onEnded = (e) => {
      // An anonymous visitor's first /auth/me is a plain 401 UNAUTHORIZED (no cookie): not a "session ended".
      // Codes that prove a session existed (ACCOUNT_INACTIVE, TOKEN_EXPIRED, ROLE_CHANGED...) always get a message.
      if (!userRef.current && e.detail?.code === 'UNAUTHORIZED') return;
      setUser(null);
      setNotice(e.detail?.code === 'ACCOUNT_INACTIVE' ? 'Your account has been deactivated.' : 'Your session has ended. Please sign in again.');
    };
    window.addEventListener(SESSION_EVENT, onEnded);
    window.addEventListener(RESET_EVENT, refresh);
    return () => {
      window.removeEventListener(SESSION_EVENT, onEnded);
      window.removeEventListener(RESET_EVENT, refresh);
    };
  }, [refresh]);

  const login = useCallback(async (identifier, password) => {
    const { user: me } = await post('/auth/login', { identifier, password });
    setNotice('');
    setUser(me);
    return me;
  }, []);

  const logout = useCallback(async () => {
    try {
      await post('/auth/logout');
    } finally {
      setUser(null);
      setNotice('');
    }
  }, []);

  const value = useMemo(
    () => ({ user, status, notice, login, logout, refresh, setUser }),
    [user, status, notice, login, logout, refresh],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
