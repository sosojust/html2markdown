import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await login(email, password);
      navigate('/');
    } catch (err) {
      setError('Login failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-base-100">
      <div className="card w-full max-w-sm shadow-xl bg-base-200">
        <div className="card-body">
          <h2 className="card-title justify-center text-2xl font-bold">Login</h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="form-control">
              <label className="label">
                <span className="label-text">Email</span>
              </label>
              <input 
                type="email" 
                className="input input-bordered w-full" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="form-control">
              <label className="label">
                <span className="label-text">Password</span>
              </label>
              <input 
                type="password" 
                className="input input-bordered w-full" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            {error && <p className="text-error text-sm">{error}</p>}
            <div className="form-control mt-6">
              <button className="btn btn-neutral w-full">Login</button>
            </div>
          </form>
          <div className="text-center mt-4">
             <Link to="/register" className="link link-hover text-sm">Create an account</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
