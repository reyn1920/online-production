import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ThemeProvider } from './contexts/ThemeContext';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ChannelProvider } from './contexts/ChannelContext';
import { AIContextProvider } from './contexts/AIContext';

// Components
import Navbar from './components/layout/Navbar';
import Sidebar from './components/layout/Sidebar';
import LoadingSpinner from './components/ui/LoadingSpinner';
import ErrorBoundary from './components/ui/ErrorBoundary';

// Pages
import LoginPage from './pages/auth/LoginPage';
import Dashboard from './pages/Dashboard';
import ChannelList from './pages/channels/ChannelList';
import ChannelDetail from './pages/channels/ChannelDetail';
import ChannelCreate from './pages/channels/ChannelCreate';
import ContentGenerator from './pages/ai/ContentGenerator';
import APIOrchestrator from './pages/api/APIOrchestrator';
import Analytics from './pages/analytics/Analytics';
import Settings from './pages/settings/Settings';
import Profile from './pages/profile/Profile';

// Styles
import './styles/globals.css';
import './styles/components.css';
import './styles/animations.css';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="large" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

// Main Layout Component
const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth < 768) {
        setSidebarOpen(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Navbar
        onMenuClick={() => setSidebarOpen(!sidebarOpen)}
        sidebarOpen={sidebarOpen}
      />

      <div className="flex">
        <Sidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
          isMobile={isMobile}
        />

        <main
          className={`flex-1 transition-all duration-300 ease-in-out ${
            sidebarOpen && !isMobile ? 'ml-64' : 'ml-0'
          }`}
        >
          <div className="p-6 pt-20">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

// App Component
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <AuthProvider>
            <ChannelProvider>
              <AIContextProvider>
                <Router>
                  <div className="App">
                    <Routes>
                      {/* Public Routes */}
                      <Route path="/login" element={<LoginPage />} />

                      {/* Protected Routes */}
                      <Route
                        path="/"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <Dashboard />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/dashboard"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <Dashboard />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/channels"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <ChannelList />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/channels/create"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <ChannelCreate />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/channels/:channelId"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <ChannelDetail />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/ai/generate"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <ContentGenerator />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/api/orchestrator"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <APIOrchestrator />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/analytics"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <Analytics />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/settings"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <Settings />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      <Route
                        path="/profile"
                        element={
                          <ProtectedRoute>
                            <MainLayout>
                              <Profile />
                            </MainLayout>
                          </ProtectedRoute>
                        }
                      />

                      {/* Catch all route */}
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>

                    {/* Global Toast Notifications */}
                    <Toaster
                      position="top-right"
                      toastOptions={{
                        duration: 4000,
                        style: {
                          background: '#363636',
                          color: '#fff',
                        },
                        success: {
                          duration: 3000,
                          iconTheme: {
                            primary: '#10B981',
                            secondary: '#fff',
                          },
                        },
                        error: {
                          duration: 5000,
                          iconTheme: {
                            primary: '#EF4444',
                            secondary: '#fff',
                          },
                        },
                      }}
                    />
                  </div>
                </Router>
              </AIContextProvider>
            </ChannelProvider>
          </AuthProvider>
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
