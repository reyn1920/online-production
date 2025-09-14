import React, { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

interface ProtectedRouteProps {
  children: ReactNode;
  requireAuth?: boolean;
  requiredRoles?: string[];
  requiredChannels?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requireAuth = true,
  requiredRoles = [],
  requiredChannels = [],
}) => {
  const { user, isAuthenticated, loading } = useAuth();
  const { actualTheme } = useTheme();
  const location = useLocation();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className={`min-h-screen flex items-center justify-center ${
        actualTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
      }`}>
        <div className="text-center">
          <div className={`animate-spin rounded-full h-12 w-12 border-b-2 mx-auto mb-4 ${
            actualTheme === 'dark' ? 'border-blue-400' : 'border-blue-600'
          }`}></div>
          <p className={actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'}>
            Loading...
          </p>
        </div>
      </div>
    );
  }

  // Redirect to login if authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check role requirements
  if (requiredRoles.length > 0 && user) {
    const hasRequiredRole = requiredRoles.some(role => user.roles.includes(role));
    if (!hasRequiredRole) {
      return (
        <div className={`min-h-screen flex items-center justify-center ${
          actualTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
        }`}>
          <div className="text-center">
            <div className="text-6xl mb-4">🚫</div>
            <h1 className={`text-2xl font-bold mb-2 ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Access Denied
            </h1>
            <p className={`mb-4 ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              You don't have the required permissions to access this page.
            </p>
            <p className={`text-sm ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Required roles: {requiredRoles.join(', ')}
            </p>
            <button
              onClick={() => window.history.back()}
              className={`mt-4 px-4 py-2 rounded-md text-sm font-medium ${
                actualTheme === 'dark'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  // Check channel access requirements
  if (requiredChannels.length > 0 && user) {
    const hasChannelAccess = requiredChannels.some(channelId => 
      user.channel_access?.includes(channelId) || false
    );
    if (!hasChannelAccess) {
      return (
        <div className={`min-h-screen flex items-center justify-center ${
          actualTheme === 'dark' ? 'bg-gray-900' : 'bg-gray-50'
        }`}>
          <div className="text-center">
            <div className="text-6xl mb-4">🔒</div>
            <h1 className={`text-2xl font-bold mb-2 ${
              actualTheme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>
              Channel Access Required
            </h1>
            <p className={`mb-4 ${
              actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-600'
            }`}>
              You don't have access to the required channels for this page.
            </p>
            <p className={`text-sm ${
              actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Required channels: {requiredChannels.join(', ')}
            </p>
            <button
              onClick={() => window.history.back()}
              className={`mt-4 px-4 py-2 rounded-md text-sm font-medium ${
                actualTheme === 'dark'
                  ? 'bg-blue-600 hover:bg-blue-700 text-white'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
              }`}
            >
              Go Back
            </button>
          </div>
        </div>
      );
    }
  }

  // If all checks pass, render the protected content
  return <>{children}</>;
};

export default ProtectedRoute;