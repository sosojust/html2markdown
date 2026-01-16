import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Link, useNavigate } from 'react-router-dom';

const Register = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { register } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [msg, setMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await register(email, password);
      setMsg('Registration successful! Redirecting to login...');
      setTimeout(() => navigate('/login'), 1500);
    } catch (err) {
      setError('Registration failed: ' + (err.response?.data?.detail || err.message));
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-base-100">
      <div className="card w-full max-w-sm shadow-xl bg-base-200">
        <div className="card-body">
          <h2 className="card-title justify-center text-2xl font-bold">Register</h2>
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
            {msg && <p className="text-success text-sm">{msg}</p>}
            <div className="form-control mt-6">
              <button className="btn btn-neutral w-full">Register</button>
            </div>
          </form>
          <div className="text-center mt-4">
             <Link to="/login" className="link link-hover text-sm">Already have an account?</Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Register;
