import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    // Check for token in URL (SSO)
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    if (urlToken) {
      localStorage.setItem('token', urlToken);
      // Clean URL immediately to hide token
      window.history.replaceState({}, document.title, window.location.pathname);
      return urlToken;
    }
    return localStorage.getItem('token');
  });
  const [loading, setLoading] = useState(true);

  const api = axios.create({
    baseURL: 'http://localhost:8000/v1',
  });

  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  const fetchUser = async () => {
    try {
      const res = await api.get('/auth/me');
      setUser(res.data);
      if (res.data.email) {
        localStorage.setItem('user_email', res.data.email);
      }
    } catch (err) {
      console.error("Failed to fetch user", err);
      logout();
    }
  };

  const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    const res = await api.post('/auth/token', formData);
    const { access_token } = res.data;
    setToken(access_token);
    localStorage.setItem('token', access_token);
    api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
    await fetchUser();
  };

  const register = async (email, password) => {
    await api.post('/auth/register', { email, password });
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user_email');
    delete api.defaults.headers.common['Authorization'];
  };

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('logout')) {
      logout();
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  useEffect(() => {
    if (token) {
       fetchUser().finally(() => setLoading(false));
    } else {
       setLoading(false);
    }
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading, api }}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
