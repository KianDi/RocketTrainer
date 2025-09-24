import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const Login: React.FC = () => {
  const [steamId, setSteamId] = useState('');
  const [username, setUsername] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!steamId.trim()) {
      setError('Steam ID is required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await login(steamId.trim(), username.trim() || undefined);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <div className="mx-auto h-12 w-12 gaming-gradient rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-xl">RT</span>
          </div>
          <h2 className="mt-6 text-center text-3xl font-gaming font-bold text-gray-900">
            Sign in to RocketTrainer
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Connect your Steam account to get started
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="steam-id" className="sr-only">
                Steam ID
              </label>
              <input
                id="steam-id"
                name="steam-id"
                type="text"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-rl-blue focus:border-rl-blue focus:z-10 sm:text-sm"
                placeholder="Steam ID (e.g., 76561198000000000)"
                value={steamId}
                onChange={(e) => setSteamId(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="username" className="sr-only">
                Username (Optional)
              </label>
              <input
                id="username"
                name="username"
                type="text"
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-rl-blue focus:border-rl-blue focus:z-10 sm:text-sm"
                placeholder="Username (optional)"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-rl-blue hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-rl-blue disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              ) : (
                'Sign in with Steam'
              )}
            </button>
          </div>

          <div className="text-center">
            <div className="text-sm text-gray-600">
              Don't have a Steam account?{' '}
              <a
                href="https://store.steampowered.com/join/"
                target="_blank"
                rel="noopener noreferrer"
                className="font-medium text-rl-blue hover:text-blue-500"
              >
                Create one here
              </a>
            </div>
          </div>
        </form>

        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300" />
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gray-50 text-gray-500">How to find your Steam ID</span>
            </div>
          </div>
          
          <div className="mt-4 text-sm text-gray-600 space-y-2">
            <p>1. Open Steam and go to your profile</p>
            <p>2. Right-click and select "Copy Page URL"</p>
            <p>3. Use a Steam ID converter to get your Steam64 ID</p>
            <p>4. Or use your custom URL (e.g., "yourname")</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
