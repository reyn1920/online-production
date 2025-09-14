import React, { useState, useEffect } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const Login: React.FC = () => {
  const [credentials, setCredentials] = useState({ username: '', password: '' });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login, isAuthenticated } = useAuth();
  const { actualTheme } = useTheme();
  const location = useLocation();
  
  // Redirect to intended page after login
  const from = (location.state as any)?.from?.pathname || '/channels';
  
  // Redirect if already authenticated
  if (isAuthenticated) {
    return <Navigate to={from} replace />;
  }
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');
    
    try {
      await login(credentials);
      // Navigation will happen automatically due to auth state change
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCredentials(prev => ({ ...prev, [name]: value }));
  };
  
  return (
    <div className={`min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 ${
      actualTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
    }`}>
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 flex items-center justify-center text-2xl">
            🚀
          </div>
          <h2 className={`mt-6 text-center text-3xl font-extrabold ${
            actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            Sign in to Trae AI Production
          </h2>
          <p className={`mt-2 text-center text-sm ${
            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            Access your enterprise-grade AI platform
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="username" className="sr-only">
                Username
              </label>
              <input
                id="username"
                name="username"
                type="text"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-t-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm ${
                  actualTheme === 'dark'
                    ? 'bg-gray-800 border-gray-600 text-white'
                    : 'bg-white border-gray-300 text-gray-900'
                }`}
                placeholder="Username"
                value={credentials.username}
                onChange={handleInputChange}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                className={`appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-b-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 focus:z-10 sm:text-sm ${
                  actualTheme === 'dark'
                    ? 'bg-gray-800 border-gray-600 text-white'
                    : 'bg-white border-gray-300 text-gray-900'
                }`}
                placeholder="Password"
                value={credentials.password}
                onChange={handleInputChange}
              />
            </div>
          </div>
          
          {error && (
            <div className={`rounded-md p-4 ${
              actualTheme === 'dark' ? 'bg-red-900 border-red-700' : 'bg-red-50 border-red-200'
            } border`}>
              <div className="flex">
                <div className="flex-shrink-0">
                  <span className="text-red-400">⚠️</span>
                </div>
                <div className="ml-3">
                  <p className={`text-sm font-medium ${
                    actualTheme === 'dark' ? 'text-red-300' : 'text-red-800'
                  }`}>
                    {error}
                  </p>
                </div>
              </div>
            </div>
          )}
          
          <div>
            <button
              type="submit"
              disabled={isLoading}
              className={`group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
                isLoading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700'
              }`}
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </button>
          </div>
          
          <div className={`text-center text-sm ${
            actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-600'
          }`}>
            <p>Demo credentials:</p>
            <p className="font-mono text-xs mt-1">
              Username: admin | Password: password
            </p>
          </div>
        </form>
        
        {/* Features showcase */}
        <div className={`mt-8 p-4 rounded-lg ${
          actualTheme === 'dark' ? 'bg-gray-800' : 'bg-white'
        } shadow`}>
          <h3 className={`text-lg font-semibold mb-3 ${
            actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}>
            🎯 Platform Features
          </h3>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div className={`flex items-center ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              <span className="mr-2">🤖</span>
              100+ Free APIs
            </div>
            <div className={`flex items-center ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              <span className="mr-2">📊</span>
              4 Core Channels
            </div>
            <div className={`flex items-center ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              <span className="mr-2">🔒</span>
              Enterprise Security
            </div>
            <div className={`flex items-center ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              <span className="mr-2">⚡</span>
              Real-time Analytics
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;