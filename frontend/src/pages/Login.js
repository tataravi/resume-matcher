import React, { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { FileText, Eye, EyeOff, AlertCircle } from 'lucide-react';
import LoadingSpinner from '../components/LoadingSpinner';

const Login = () => {
  const { login, getDemoAccess, isAuthenticated } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await login(formData.email, formData.password);
      // Redirect will happen automatically via auth context
    } catch (error) {
      setError(
        error.response?.data?.detail || 
        'Login failed. Please check your credentials.'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDemoAccess = async () => {
    setLoading(true);
    setError('');

    try {
      await getDemoAccess();
      // Redirect will happen automatically via auth context
    } catch (error) {
      setError('Failed to get demo access. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center rounded-full bg-primary-100">
            <FileText className="h-8 w-8 text-primary-600" />
          </div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Sign in to Resume Analyzer
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Analyze your resume with AI-powered insights
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="h-5 w-5 text-red-400" />
              <div className="ml-3">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            </div>
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4">
            <div>
              <label htmlFor="email" className="label">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="input"
                placeholder="Enter your email"
                value={formData.email}
                onChange={handleChange}
                disabled={loading}
              />
            </div>

            <div>
              <label htmlFor="password" className="label">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  className="input pr-10"
                  placeholder="Enter your password"
                  value={formData.password}
                  onChange={handleChange}
                  disabled={loading}
                />
                <button
                  type="button"
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={loading}
                >
                  {showPassword ? (
                    <EyeOff className="h-5 w-5 text-gray-400" />
                  ) : (
                    <Eye className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              </div>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <LoadingSpinner size="sm" />
              ) : (
                'Sign in'
              )}
            </button>
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">Or</span>
            </div>
          </div>

          <div>
            <button
              type="button"
              onClick={handleDemoAccess}
              disabled={loading}
              className="group relative w-full flex justify-center btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <LoadingSpinner size="sm" />
              ) : (
                'Try Demo (No Registration)'
              )}
            </button>
          </div>

          <div className="text-center">
            <p className="text-sm text-gray-600">
              Demo accounts available:
            </p>
            <div className="mt-2 space-y-1 text-xs text-gray-500">
              <p>admin@example.com / admin123</p>
              <p>user@example.com / user123</p>
            </div>
          </div>

          <div className="text-center">
            <Link
              to="/register"
              className="text-primary-600 hover:text-primary-500 text-sm font-medium"
            >
              Don't have an account? Sign up
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Login;