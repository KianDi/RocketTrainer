import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { 
  ChartBarIcon, 
  TrophyIcon, 
  ClockIcon,
  FireIcon
} from '@heroicons/react/24/outline';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // Mock data for MVP
  const stats = {
    totalMatches: 47,
    winRate: 68.1,
    currentRank: user?.current_rank || 'Diamond II',
    hoursPlayed: 156,
    weaknesses: [
      { name: 'Aerial Accuracy', score: 65, improvement: '+12%' },
      { name: 'Save Percentage', score: 72, improvement: '+8%' },
      { name: 'Positioning', score: 58, improvement: '+15%' }
    ],
    recentMatches: [
      { id: 1, result: 'Win', score: '3-1', playlist: 'Ranked 2v2', date: '2 hours ago' },
      { id: 2, result: 'Loss', score: '1-4', playlist: 'Ranked 2v2', date: '4 hours ago' },
      { id: 3, result: 'Win', score: '2-0', playlist: 'Ranked 2v2', date: '1 day ago' },
    ]
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-gaming font-bold text-gray-900">
            Welcome back, {user?.username}!
          </h1>
          <p className="text-gray-600 mt-2">
            Here's your Rocket League performance overview
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="stat-card">
            <div className="flex items-center">
              <div className="p-2 bg-rl-blue rounded-lg">
                <TrophyIcon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Current Rank</p>
                <p className="text-2xl font-bold text-gray-900">{stats.currentRank}</p>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center">
              <div className="p-2 bg-rl-green rounded-lg">
                <ChartBarIcon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Win Rate</p>
                <p className="text-2xl font-bold text-gray-900">{stats.winRate}%</p>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center">
              <div className="p-2 bg-rl-purple rounded-lg">
                <FireIcon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Matches</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalMatches}</p>
              </div>
            </div>
          </div>

          <div className="stat-card">
            <div className="flex items-center">
              <div className="p-2 bg-rl-orange rounded-lg">
                <ClockIcon className="w-6 h-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Hours Played</p>
                <p className="text-2xl font-bold text-gray-900">{stats.hoursPlayed}</p>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Weaknesses Analysis */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Areas for Improvement</h2>
            <div className="space-y-4">
              {stats.weaknesses.map((weakness, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm font-medium text-gray-700">
                        {weakness.name}
                      </span>
                      <span className="text-sm text-green-600 font-medium">
                        {weakness.improvement}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-rl-blue h-2 rounded-full transition-all duration-300"
                        style={{ width: `${weakness.score}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-6">
              <button className="btn-primary w-full">
                Get Training Recommendations
              </button>
            </div>
          </div>

          {/* Recent Matches */}
          <div className="card">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Matches</h2>
            <div className="space-y-3">
              {stats.recentMatches.map((match) => (
                <div key={match.id} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      match.result === 'Win' ? 'bg-green-500' : 'bg-red-500'
                    }`}></div>
                    <div>
                      <p className="font-medium text-gray-900">
                        {match.result} {match.score}
                      </p>
                      <p className="text-sm text-gray-600">{match.playlist}</p>
                    </div>
                  </div>
                  <span className="text-sm text-gray-500">{match.date}</span>
                </div>
              ))}
            </div>
            <div className="mt-4">
              <button className="text-rl-blue hover:text-blue-700 text-sm font-medium">
                View all matches →
              </button>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="card text-center">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Upload Replay</h3>
            <p className="text-gray-600 mb-4">Analyze your latest matches</p>
            <button className="btn-primary">Upload Now</button>
          </div>

          <div className="card text-center">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Start Training</h3>
            <p className="text-gray-600 mb-4">Practice your weak areas</p>
            <button className="btn-primary">View Packs</button>
          </div>

          <div className="card text-center">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Find Partners</h3>
            <p className="text-gray-600 mb-4">Train with similar players</p>
            <button className="btn-primary">Match Me</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
