import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { replayService } from '../services/replayService';
import { ReplayAnalysis, CoachingInsights } from '../types';
import CoachingInsightsSection from '../components/CoachingInsightsSection';

const MatchAnalysisPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [analysis, setAnalysis] = useState<ReplayAnalysis | null>(null);
  const [coachingInsights, setCoachingInsights] = useState<CoachingInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [insightsError, setInsightsError] = useState<string | null>(null);

  const fetchCoachingInsights = async (replayId: string) => {
    try {
      setInsightsLoading(true);
      setInsightsError(null);
      const response = await replayService.getCoachingInsights(replayId);
      if (response.success && response.insights) {
        setCoachingInsights(response.insights);
      } else {
        setInsightsError(response.error_message || 'Failed to load coaching insights');
      }
    } catch (err) {
      console.error('Failed to fetch coaching insights:', err);
      setInsightsError(err instanceof Error ? err.message : 'Failed to load coaching insights');
    } finally {
      setInsightsLoading(false);
    }
  };

  useEffect(() => {
    const fetchAnalysis = async () => {
      if (!id) {
        setError('No replay ID provided');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        const data = await replayService.getReplayAnalysis(id);
        setAnalysis(data);

        // Fetch coaching insights after analysis is loaded
        fetchCoachingInsights(id);
      } catch (err) {
        console.error('Failed to fetch replay analysis:', err);
        setError(err instanceof Error ? err.message : 'Failed to load replay analysis');
      } finally {
        setLoading(false);
      }
    };

    fetchAnalysis();
  }, [id]);

  const handleRetry = () => {
    if (id) {
      setError(null);
      setLoading(true);
      // Re-trigger the effect by updating a dependency
      const fetchAnalysis = async () => {
        try {
          const data = await replayService.getReplayAnalysis(id);
          setAnalysis(data);
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Failed to load replay analysis');
        } finally {
          setLoading(false);
        }
      };
      fetchAnalysis();
    }
  };

  const formatDuration = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const formatPercentage = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return `${Math.round(value * 100)}%`;
  };

  const formatScore = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return value.toString();
  };

  const formatSpeed = (value?: number): string => {
    if (value === undefined || value === null) return 'N/A';
    return `${Math.round(value)} uu/s`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
                <div className="space-y-3">
                  {[...Array(6)].map((_, i) => (
                    <div key={i} className="h-4 bg-gray-200 rounded"></div>
                  ))}
                </div>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
                <div className="h-64 bg-gray-200 rounded"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-center">
              <div className="text-red-600 text-xl font-semibold mb-4">
                Error Loading Analysis
              </div>
              <p className="text-gray-600 mb-6">{error}</p>
              <div className="space-x-4">
                <button
                  onClick={handleRetry}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg"
                >
                  Try Again
                </button>
                <button
                  onClick={() => navigate('/replays')}
                  className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
                >
                  Back to Replays
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!analysis) {
    return (
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-center text-gray-600">
              No analysis data available
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Breadcrumb Navigation */}
        <nav className="mb-6">
          <ol className="flex items-center space-x-2 text-sm text-gray-500">
            <li>
              <button onClick={() => navigate('/')} className="hover:text-blue-600">
                Home
              </button>
            </li>
            <li>/</li>
            <li>
              <button onClick={() => navigate('/replays')} className="hover:text-blue-600">
                Replays
              </button>
            </li>
            <li>/</li>
            <li className="text-gray-900 font-medium">
              {analysis.filename || 'Analysis'}
            </li>
          </ol>
        </nav>

        {/* Match Header */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {analysis.filename || 'Replay Analysis'}
              </h1>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="capitalize">{analysis.playlist.replace('_', ' ')}</span>
                <span>•</span>
                <span className={`font-semibold ${
                  analysis.result === 'win' ? 'text-green-600' : 
                  analysis.result === 'loss' ? 'text-red-600' : 'text-yellow-600'
                }`}>
                  {analysis.result.toUpperCase()} {analysis.score}
                </span>
                <span>•</span>
                <span>{formatDuration(analysis.duration)} duration</span>
                {analysis.match_date && (
                  <>
                    <span>•</span>
                    <span>{new Date(analysis.match_date).toLocaleDateString()}</span>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Performance Overview */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {formatScore(analysis.player_stats.score)}
              </div>
              <div className="text-sm text-gray-600">Score</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {formatScore(analysis.player_stats.goals)}
              </div>
              <div className="text-sm text-gray-600">Goals</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {formatScore(analysis.player_stats.saves)}
              </div>
              <div className="text-sm text-gray-600">Saves</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {formatPercentage(analysis.player_stats.boost_efficiency)}
              </div>
              <div className="text-sm text-gray-600">Boost Efficiency</div>
            </div>
          </div>
        </div>

        {/* Detailed Statistics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Core Statistics</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Goals:</span>
                <span className="font-medium">{formatScore(analysis.player_stats.goals)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Assists:</span>
                <span className="font-medium">{formatScore(analysis.player_stats.assists)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Saves:</span>
                <span className="font-medium">{formatScore(analysis.player_stats.saves)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Shots:</span>
                <span className="font-medium">{formatScore(analysis.player_stats.shots)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Score:</span>
                <span className="font-medium">{formatScore(analysis.player_stats.score)}</span>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Movement & Positioning</h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Average Speed:</span>
                <span className="font-medium">{formatSpeed(analysis.player_stats.average_speed)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Time Supersonic:</span>
                <span className="font-medium">{formatPercentage(analysis.player_stats.time_supersonic)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Ground Time:</span>
                <span className="font-medium">{formatPercentage(analysis.player_stats.time_on_ground)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Low Air Time:</span>
                <span className="font-medium">{formatPercentage(analysis.player_stats.time_low_air)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">High Air Time:</span>
                <span className="font-medium">{formatPercentage(analysis.player_stats.time_high_air)}</span>
              </div>
            </div>
          </div>
        </div>

        {/* AI Analysis Scores */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">AI Performance Analysis</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {formatPercentage(analysis.player_stats.positioning_score)}
              </div>
              <div className="text-sm text-gray-600">Positioning</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {formatPercentage(analysis.player_stats.rotation_score)}
              </div>
              <div className="text-sm text-gray-600">Rotation</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {formatPercentage(analysis.player_stats.aerial_efficiency)}
              </div>
              <div className="text-sm text-gray-600">Aerial Efficiency</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {formatPercentage(analysis.player_stats.boost_efficiency)}
              </div>
              <div className="text-sm text-gray-600">Boost Efficiency</div>
            </div>
          </div>
        </div>

        {/* Action Counts */}
        {(analysis.player_stats.defensive_actions || analysis.player_stats.offensive_actions) && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Action Analysis</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {formatScore(analysis.player_stats.defensive_actions)}
                </div>
                <div className="text-sm text-gray-600">Defensive Actions</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {formatScore(analysis.player_stats.offensive_actions)}
                </div>
                <div className="text-sm text-gray-600">Offensive Actions</div>
              </div>
            </div>
          </div>
        )}

        {/* AI Coaching Insights Section */}
        {coachingInsights && (
          <CoachingInsightsSection
            insights={coachingInsights}
            isLoading={insightsLoading}
          />
        )}

        {/* Coaching Insights Loading State */}
        {insightsLoading && !coachingInsights && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
              <div className="space-y-4">
                <div className="h-20 bg-gray-200 rounded"></div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-32 bg-gray-200 rounded"></div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Coaching Insights Error State */}
        {insightsError && !coachingInsights && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="text-center">
              <div className="text-yellow-500 text-4xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                Coaching Insights Unavailable
              </h3>
              <p className="text-gray-600 mb-4">{insightsError}</p>
              <button
                onClick={() => id && fetchCoachingInsights(id)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg"
              >
                Retry Analysis
              </button>
            </div>
          </div>
        )}

        {/* Back Button */}
        <div className="text-center">
          <button
            onClick={() => navigate('/replays')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-2 rounded-lg"
          >
            Back to Replays
          </button>
        </div>
      </div>
    </div>
  );
};

export default MatchAnalysisPage;
