import React, { ReactNode } from 'react';
import { useTheme } from '../contexts/ThemeContext';
import { useAuth } from '../contexts/AuthContext';
import { useChannel } from '../contexts/ChannelContext';

interface LayoutProps {
  children: ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { actualTheme, toggleTheme } = useTheme();
  const { user, logout } = useAuth();
  const { state: channelState } = useChannel();

  return (
    <div className={`min-h-screen ${actualTheme === 'dark' ? 'dark bg-gray-900 text-white' : 'bg-gray-50 text-gray-900'}`}>
      {/* Header */}
      <header className={`${actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-b`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <h1 className="text-xl font-bold">
                🚀 Trae AI Production
              </h1>
            </div>

            {/* Navigation */}
            <nav className="hidden md:flex space-x-8">
              <a href="/channels" className={`${actualTheme === 'dark' ? 'text-gray-300 hover:text-white' : 'text-gray-500 hover:text-gray-900'} px-3 py-2 rounded-md text-sm font-medium`}>
                Channels ({channelState.channels.length})
              </a>
              <a href="/ai-content" className={`${actualTheme === 'dark' ? 'text-gray-300 hover:text-white' : 'text-gray-500 hover:text-gray-900'} px-3 py-2 rounded-md text-sm font-medium`}>
                AI Content
              </a>
              <a href="/api-orchestration" className={`${actualTheme === 'dark' ? 'text-gray-300 hover:text-white' : 'text-gray-500 hover:text-gray-900'} px-3 py-2 rounded-md text-sm font-medium`}>
                API Services
              </a>
              <a href="/analytics" className={`${actualTheme === 'dark' ? 'text-gray-300 hover:text-white' : 'text-gray-500 hover:text-gray-900'} px-3 py-2 rounded-md text-sm font-medium`}>
                Analytics
              </a>
            </nav>

            {/* User menu */}
            <div className="flex items-center space-x-4">
              {/* Theme toggle */}
              <button
                onClick={toggleTheme}
                className={`p-2 rounded-md ${actualTheme === 'dark' ? 'text-gray-300 hover:text-white hover:bg-gray-700' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'}`}
              >
                {actualTheme === 'dark' ? '☀️' : '🌙'}
              </button>

              {/* User info */}
              {user && (
                <div className="flex items-center space-x-3">
                  <span className={`text-sm ${actualTheme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                    {user.username}
                  </span>
                  <button
                    onClick={logout}
                    className={`px-3 py-1 rounded-md text-sm font-medium ${
                      actualTheme === 'dark'
                        ? 'bg-red-600 hover:bg-red-700 text-white'
                        : 'bg-red-500 hover:bg-red-600 text-white'
                    }`}
                  >
                    Logout
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {children}
      </main>

      {/* Footer */}
      <footer className={`${actualTheme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} border-t mt-auto`}>
        <div className="max-w-7xl mx-auto py-4 px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <p className={`text-sm ${actualTheme === 'dark' ? 'text-gray-400' : 'text-gray-500'}`}>
              © 2024 Trae AI Production. Powered by 100+ Free APIs.
            </p>
            <div className="flex space-x-4">
              <span className={`text-xs px-2 py-1 rounded ${
                actualTheme === 'dark' ? 'bg-green-900 text-green-300' : 'bg-green-100 text-green-800'
              }`}>
                ✅ Production Ready
              </span>
              <span className={`text-xs px-2 py-1 rounded ${
                actualTheme === 'dark' ? 'bg-blue-900 text-blue-300' : 'bg-blue-100 text-blue-800'
              }`}>
                🔒 Enterprise Security
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
