import React, { useState, useEffect } from 'react';
import {
  PlayIcon,
  ChartBarIcon,
  TrashIcon,
  ClockIcon,
  TrophyIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import ReplayUpload from '../components/ReplayUpload';
import { replayService, ReplayResponse } from '../services/replayService';

const Replays: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'upload' | 'manage'>('upload');
  const [replays, setReplays] = useState<ReplayResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (activeTab === 'manage') {
      loadReplays();
    }
  }, [activeTab]);

  const loadReplays = async () => {
    setLoading(true);
    setError(null);
    try {
      const userReplays = await replayService.getUserReplays();
      setReplays(userReplays);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load replays');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadComplete = (replayId: string) => {
    // Refresh replays list if we're on the manage tab
    if (activeTab === 'manage') {
      loadReplays();
    }
    // Show success message
    console.log('Upload completed:', replayId);
  };

  const handleUploadError = (error: string) => {
    setError(error);
  };

  const handleDeleteReplay = async (replayId: string) => {
    if (!window.confirm('Are you sure you want to delete this replay?')) {
      return;
    }

    try {
      await replayService.deleteReplay(replayId);
      setReplays(prev => prev.filter(replay => replay.id !== replayId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete replay');
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processed':
        return <ChartBarIcon className="w-5 h-5 text-green-500" />;
      case 'processing':
        return <ArrowPathIcon className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <ExclamationTriangleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'processed':
        return 'Analysis Complete';
      case 'processing':
        return 'Processing...';
      case 'failed':
        return 'Processing Failed';
      default:
        return 'Unknown';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-gaming font-bold text-gray-900 mb-4">
            Replay Analysis
          </h1>
          <p className="text-gray-600">
            Upload your Rocket League replays to get AI-powered analysis and personalized training recommendations.
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mr-2" />
              <p className="text-red-700">{error}</p>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="mb-8">
          <nav className="flex space-x-8">
            <button
              onClick={() => setActiveTab('upload')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'upload'
                  ? 'border-rl-blue text-rl-blue'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Upload Replays
            </button>
            <button
              onClick={() => setActiveTab('manage')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'manage'
                  ? 'border-rl-blue text-rl-blue'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Manage Replays
            </button>
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'upload' && (
          <div className="space-y-8">
            <div className="card">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                Upload New Replays
              </h2>
              <ReplayUpload
                onUploadComplete={handleUploadComplete}
                onUploadError={handleUploadError}
              />
            </div>

            <div className="card">
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                How It Works
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <PlayIcon className="w-6 h-6 text-rl-blue" />
                  </div>
                  <h4 className="font-medium text-gray-900 mb-2">1. Upload Replay</h4>
                  <p className="text-sm text-gray-600">
                    Drag and drop your .replay files or click to select them
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <ArrowPathIcon className="w-6 h-6 text-rl-blue" />
                  </div>
                  <h4 className="font-medium text-gray-900 mb-2">2. AI Analysis</h4>
                  <p className="text-sm text-gray-600">
                    Our AI analyzes your gameplay to identify strengths and weaknesses
                  </p>
                </div>
                <div className="text-center">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-3">
                    <TrophyIcon className="w-6 h-6 text-rl-blue" />
                  </div>
                  <h4 className="font-medium text-gray-900 mb-2">3. Get Insights</h4>
                  <p className="text-sm text-gray-600">
                    Receive personalized training recommendations to improve your game
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'manage' && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900">
                Your Replays ({replays.length})
              </h2>
              <button
                onClick={loadReplays}
                disabled={loading}
                className="btn-secondary flex items-center space-x-2"
              >
                <ArrowPathIcon className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>

            {loading ? (
              <div className="card text-center py-12">
                <ArrowPathIcon className="w-8 h-8 animate-spin mx-auto mb-4 text-gray-400" />
                <p className="text-gray-600">Loading replays...</p>
              </div>
            ) : replays.length === 0 ? (
              <div className="card text-center py-12">
                <PlayIcon className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No replays yet</h3>
                <p className="text-gray-600 mb-4">
                  Upload your first replay to get started with AI analysis
                </p>
                <button
                  onClick={() => setActiveTab('upload')}
                  className="btn-primary"
                >
                  Upload Replay
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4">
                {replays.map((replay) => (
                  <div key={replay.id} className="card">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        {getStatusIcon(replay.status)}
                        <div>
                          <h3 className="font-medium text-gray-900">
                            {replay.filename || `Replay ${replay.id.slice(0, 8)}`}
                          </h3>
                          <div className="flex items-center space-x-4 text-sm text-gray-600">
                            <span>{getStatusText(replay.status)}</span>
                            {replay.playlist && (
                              <span>• {replay.playlist}</span>
                            )}
                            {replay.result && (
                              <span>• {replay.result}</span>
                            )}
                            <span>• {formatDate(replay.uploaded_at)}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        {replay.status === 'processed' && (
                          <button
                            onClick={() => {/* TODO: Navigate to analysis */}}
                            className="btn-secondary text-sm"
                          >
                            View Analysis
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteReplay(replay.id)}
                          className="text-red-500 hover:text-red-700 p-2"
                          title="Delete replay"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Replays;
