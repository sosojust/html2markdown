import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(() => {
    // Check for token in URL (SSO)
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    const urlRefreshToken = params.get('refresh_token');
    
    if (urlToken) {
      localStorage.setItem('token', urlToken);
      if (urlRefreshToken) {
        localStorage.setItem('refresh_token', urlRefreshToken);
      }
      // Clean URL immediately to hide token
      window.history.replaceState({}, document.title, window.location.pathname);
      return urlToken;
    }
    return localStorage.getItem('token');
  });
  const [loading, setLoading] = useState(true);

  const api = axios.create({
    baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1',
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
    const { access_token, refresh_token } = res.data;
    setToken(access_token);
    localStorage.setItem('token', access_token);
    if (refresh_token) {
      localStorage.setItem('refresh_token', refresh_token);
    }
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
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_email');
    delete api.defaults.headers.common['Authorization'];
  };

  // Add interceptor for 401 refresh logic
  useEffect(() => {
    const interceptor = api.interceptors.response.use(
      (response) => response,
      async (error) => {
        const originalRequest = error.config;
        
        // Prevent infinite loop
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          const refreshToken = localStorage.getItem('refresh_token');
          if (refreshToken) {
            try {
              // Call refresh endpoint
              // Note: We use a fresh axios instance or direct fetch to avoid interceptor loop,
              // but here we just need to ensure we don't use the expired token if possible?
              // Actually, api instance is fine as long as we don't attach bad headers or the refresh endpoint is public/different.
              // But /refresh needs no auth header? It takes body.
              // However, our api instance has the old Authorization header attached.
              // Let's temporarily unset it or create a new instance?
              // Simple fetch is safer.
              const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/v1';
              const resp = await fetch(`${baseURL}/auth/refresh`, {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json'
                },
                body: JSON.stringify({ refresh_token: refreshToken })
              });
              
              if (resp.ok) {
                const data = await resp.json();
                const { access_token, refresh_token: new_refresh_token } = data;
                
                // Update state
                setToken(access_token);
                localStorage.setItem('token', access_token);
                if (new_refresh_token) {
                  localStorage.setItem('refresh_token', new_refresh_token);
                }
                
                // Update defaults
                api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
                
                // Retry original request
                originalRequest.headers['Authorization'] = `Bearer ${access_token}`;
                return api(originalRequest);
              } else {
                 // Refresh failed
                 logout();
              }
            } catch (refreshError) {
              console.error("Token refresh failed:", refreshError);
              logout();
            }
          } else {
             logout();
          }
        }
        return Promise.reject(error);
      }
    );
    
    return () => {
      api.interceptors.response.eject(interceptor);
    };
  }, [api]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('logout')) {
      logout();
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  useEffect(() => {
    if (token) {
       // Validate token integrity (e.g. check for refresh token presence)
       // If we have token but no refresh token, and it's not a fresh SSO login (which might not have refresh token yet? No, SSO sets token only)
       // Wait, SSO logic sets token in useState initializer.
       // If this is a legacy login session, force logout to get refresh token.
       const hasRefreshToken = !!localStorage.getItem('refresh_token');
       if (!hasRefreshToken) {
          console.warn("Legacy session detected (no refresh token). Logging out to force re-auth.");
          logout();
          setLoading(false);
          return;
       }

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
