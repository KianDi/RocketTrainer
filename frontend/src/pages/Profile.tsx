import React from 'react';
import { useAuth } from '../contexts/AuthContext';

const Profile: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-gaming font-bold text-gray-900 mb-8">
          Profile Settings
        </h1>
        
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 mb-6">
            Account Information
          </h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Username
              </label>
              <input
                type="text"
                value={user?.username || ''}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-rl-blue focus:border-rl-blue"
                readOnly
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Steam ID
              </label>
              <input
                type="text"
                value={user?.steam_id || ''}
                className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50"
                readOnly
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Current Rank
              </label>
              <input
                type="text"
                value={user?.current_rank || 'Not set'}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-rl-blue focus:border-rl-blue"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Account Type
              </label>
              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                user?.is_premium 
                  ? 'bg-yellow-100 text-yellow-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {user?.is_premium ? 'Premium' : 'Free'}
              </span>
            </div>
          </div>
          
          <div className="mt-6 flex space-x-4">
            <button className="btn-primary">
              Save Changes
            </button>
            <button className="btn-secondary">
              Cancel
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile;
