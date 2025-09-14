import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface SidebarItem {
  name: string;
  path: string;
  icon?: string;
}

const sidebarItems: SidebarItem[] = [
  { name: 'Dashboard', path: '/dashboard' },
  { name: 'Channels', path: '/channels' },
  { name: 'AI Content', path: '/ai' },
  { name: 'API', path: '/api' },
  { name: 'Analytics', path: '/analytics' },
  { name: 'Settings', path: '/settings' },
  { name: 'Profile', path: '/profile' },
];

const Sidebar: React.FC = () => {
  const location = useLocation();

  return (
    <div className="bg-gray-800 text-white w-64 min-h-screen p-4">
      <nav className="space-y-2">
        {sidebarItems.map((item) => {
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`block px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-gray-900 text-white'
                  : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>
    </div>
  );
};

export default Sidebar;