import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { 
  HomeIcon, 
  ChartBarIcon, 
  VideoCameraIcon, 
  AcademicCapIcon,
  UserIcon,
  ArrowRightOnRectangleIcon
} from '@heroicons/react/24/outline';

const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <nav className="bg-white shadow-lg border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link to="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 gaming-gradient rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">RT</span>
              </div>
              <span className="font-gaming text-xl font-bold text-gray-900">
                RocketTrainer
              </span>
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            {user ? (
              <>
                <Link
                  to="/dashboard"
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-rl-blue hover:bg-gray-100 transition-colors"
                >
                  <ChartBarIcon className="w-4 h-4" />
                  <span>Dashboard</span>
                </Link>
                
                <Link
                  to="/replays"
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-rl-blue hover:bg-gray-100 transition-colors"
                >
                  <VideoCameraIcon className="w-4 h-4" />
                  <span>Replays</span>
                </Link>
                
                <Link
                  to="/training"
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-rl-blue hover:bg-gray-100 transition-colors"
                >
                  <AcademicCapIcon className="w-4 h-4" />
                  <span>Training</span>
                </Link>
                
                <Link
                  to="/profile"
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-rl-blue hover:bg-gray-100 transition-colors"
                >
                  <UserIcon className="w-4 h-4" />
                  <span>{user.username}</span>
                </Link>
                
                <button
                  onClick={handleLogout}
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-red-600 hover:bg-gray-100 transition-colors"
                >
                  <ArrowRightOnRectangleIcon className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/"
                  className="flex items-center space-x-1 px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-rl-blue hover:bg-gray-100 transition-colors"
                >
                  <HomeIcon className="w-4 h-4" />
                  <span>Home</span>
                </Link>
                
                <Link
                  to="/login"
                  className="btn-primary"
                >
                  Login with Steam
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
