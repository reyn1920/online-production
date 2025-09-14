import React from 'react';
import { useAuth } from '../../contexts/AuthContext';

const Profile: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Profile</h1>
      <div className="bg-white shadow rounded-lg p-6">
        {user ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Username</label>
              <p className="mt-1 text-sm text-gray-900">{user.username}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">User ID</label>
              <p className="mt-1 text-sm text-gray-900">{user.user_id}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Roles</label>
              <p className="mt-1 text-sm text-gray-900">{user.roles.join(', ')}</p>
            </div>
          </div>
        ) : (
          <p className="text-gray-600">No user information available.</p>
        )}
      </div>
    </div>
  );
};

export default Profile;