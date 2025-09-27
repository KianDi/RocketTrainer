import React, { useState } from 'react';
import {
  AcademicCapIcon,
  StarIcon,
  ArrowTopRightOnSquareIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  TrophyIcon
} from '@heroicons/react/24/outline';
import { useTrainingRecommendations } from '../hooks/useMLApi';
import { mlService } from '../services/mlService';
import { TrainingRecommendationItem } from '../types';

interface TrainingRecommendationsProps {
  weaknessAnalysis?: any;
  className?: string;
}

const TrainingRecommendations: React.FC<TrainingRecommendationsProps> = ({ 
  weaknessAnalysis,
  className = '' 
}) => {
  const { data, loading, error, getRecommendations, clearError } = useTrainingRecommendations();
  const [skillLevel, setSkillLevel] = useState<string>('');
  const [maxRecommendations, setMaxRecommendations] = useState<number>(5);
  const [focusAreas, setFocusAreas] = useState<string[]>([]);

  const skillLevels = [
    'bronze', 'silver', 'gold', 'platinum', 'diamond', 'champion', 'grand_champion', 'supersonic_legend'
  ];

  const availableFocusAreas = React.useMemo(() => [
    'mechanical', 'positioning', 'game_sense', 'aerial', 'ground_play', 'saves', 'shooting'
  ], []);

  const handleGetRecommendations = async () => {
    const request: any = {
      max_recommendations: maxRecommendations,
    };

    if (skillLevel) {
      request.skill_level = skillLevel;
    }

    if (focusAreas.length > 0) {
      request.focus_areas = focusAreas;
    }

    await getRecommendations(request);
  };

  const toggleFocusArea = (area: string) => {
    setFocusAreas(prev => 
      prev.includes(area) 
        ? prev.filter(a => a !== area)
        : [...prev, area]
    );
  };

  const getDifficultyColor = (difficulty: number): string => {
    if (!difficulty) return 'bg-gray-100 text-gray-800';

    switch (difficulty) {
      case 1: return 'bg-green-100 text-green-800';
      case 2: return 'bg-green-100 text-green-800';
      case 3: return 'bg-yellow-100 text-yellow-800';
      case 4: return 'bg-orange-100 text-orange-800';
      case 5: return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDifficultyLabel = (difficulty: number): string => {
    if (!difficulty) return 'Unknown';

    switch (difficulty) {
      case 1: return 'Beginner';
      case 2: return 'Easy';
      case 3: return 'Intermediate';
      case 4: return 'Advanced';
      case 5: return 'Expert';
      default: return 'Unknown';
    }
  };

  const getRelevanceStars = (score: number): number => {
    return Math.round(score * 5);
  };

  const copyTrainingCode = (code: string) => {
    navigator.clipboard.writeText(code);
    // You could add a toast notification here
  };

  // Auto-populate from weakness analysis
  React.useEffect(() => {
    if (weaknessAnalysis && !skillLevel) {
      // Try to infer skill level from weakness analysis or user data
      setSkillLevel('platinum'); // Default fallback

      // Auto-set focus areas based on weaknesses
      const weaknesses = [weaknessAnalysis.primary_weakness, weaknessAnalysis.secondary_weakness]
        .filter(w => w && typeof w === 'string'); // Filter out undefined/null values

      const mappedAreas = weaknesses
        .map(w => w.toLowerCase().replace(/\s+/g, '_'))
        .filter(area => availableFocusAreas.includes(area));

      if (mappedAreas.length > 0) {
        setFocusAreas(mappedAreas);
      }
    }
  }, [weaknessAnalysis, skillLevel, availableFocusAreas]);

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <AcademicCapIcon className="w-6 h-6 text-rl-blue" />
          <h2 className="text-xl font-bold text-gray-900">AI Training Recommendations</h2>
        </div>
        
        {data && (
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <TrophyIcon className="w-4 h-4" />
            <span>{data.recommendations.length} recommendations</span>
            {data.cache_hit && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                Cached
              </span>
            )}
          </div>
        )}
      </div>

      {/* Configuration */}
      <div className="mb-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Skill Level
            </label>
            <select
              value={skillLevel}
              onChange={(e) => setSkillLevel(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-rl-blue"
              disabled={loading}
            >
              <option value="">Auto-detect</option>
              {skillLevels.map(level => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1).replace('_', ' ')}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Max Recommendations
            </label>
            <select
              value={maxRecommendations}
              onChange={(e) => setMaxRecommendations(Number(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-rl-blue"
              disabled={loading}
            >
              <option value={3}>3 recommendations</option>
              <option value={5}>5 recommendations</option>
              <option value={10}>10 recommendations</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Focus Areas (optional)
          </label>
          <div className="flex flex-wrap gap-2">
            {availableFocusAreas.map(area => (
              <button
                key={area}
                onClick={() => toggleFocusArea(area)}
                disabled={loading}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                  focusAreas.includes(area)
                    ? 'bg-rl-blue text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {area.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={handleGetRecommendations}
          disabled={loading}
          className="btn-primary flex items-center space-x-2"
        >
          {loading ? (
            <>
              <ArrowPathIcon className="w-4 h-4 animate-spin" />
              <span>Getting Recommendations...</span>
            </>
          ) : (
            <>
              <AcademicCapIcon className="w-4 h-4" />
              <span>Get AI Recommendations</span>
            </>
          )}
        </button>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-start space-x-3">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-500 mt-0.5" />
            <div className="flex-1">
              <h3 className="text-sm font-medium text-red-800">
                {mlService.isRateLimitError(error) ? 'Rate Limit Exceeded' : 'Recommendations Failed'}
              </h3>
              <p className="text-sm text-red-700 mt-1">
                {mlService.getErrorMessage(error)}
              </p>
            </div>
            <button
              onClick={clearError}
              className="text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Recommendations */}
      {data && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-rl-blue">
                  {data.total_packs_evaluated}
                </div>
                <div className="text-sm text-gray-600">Packs Evaluated</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {data.skill_level_detected ?
                    data.skill_level_detected.charAt(0).toUpperCase() + data.skill_level_detected.slice(1).replace('_', ' ') :
                    'Unknown'
                  }
                </div>
                <div className="text-sm text-gray-600">Detected Skill Level</div>
              </div>
            </div>
          </div>

          {/* Training Packs */}
          <div className="space-y-4">
            {data.recommendations.map((item: TrainingRecommendationItem, index: number) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h3 className="text-lg font-semibold text-gray-900">{item.name}</h3>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getDifficultyColor(item.difficulty)}`}>
                        {getDifficultyLabel(item.difficulty)}
                      </span>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mb-2">
                      <span>{item.category}</span>
                      <span>•</span>
                      <span>Quality: {Math.round(item.quality_score * 100)}%</span>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="flex items-center space-x-1 mb-1">
                      {[...Array(5)].map((_, i) => (
                        <StarIcon
                          key={i}
                          className={`w-4 h-4 ${
                            i < getRelevanceStars(item.overall_score)
                              ? 'text-yellow-400 fill-current'
                              : 'text-gray-300'
                          }`}
                        />
                      ))}
                    </div>
                    <div className="text-xs text-gray-500">
                      {Math.round(item.overall_score * 100)}% overall
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-3 mb-3">
                  <p className="text-sm text-blue-800">
                    <strong>Why this helps:</strong> {item.reasoning}
                  </p>
                  {item.estimated_improvement && (
                    <p className="text-sm text-blue-700 mt-1">
                      <strong>Expected improvement:</strong> {Math.round(item.estimated_improvement * 100)}%
                    </p>
                  )}
                  <div className="flex items-center space-x-4 text-xs text-blue-600 mt-2">
                    <span>Relevance: {Math.round(item.relevance_score * 100)}%</span>
                    <span>Difficulty Match: {Math.round(item.difficulty_match * 100)}%</span>
                  </div>
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium text-gray-700">Training Code:</span>
                    <code className="px-2 py-1 bg-gray-100 rounded text-sm font-mono">
                      {item.code}
                    </code>
                    <button
                      onClick={() => copyTrainingCode(item.code)}
                      className="text-rl-blue hover:text-blue-700 text-sm"
                    >
                      Copy
                    </button>
                  </div>
                  
                  <button className="flex items-center space-x-1 text-rl-blue hover:text-blue-700 text-sm font-medium">
                    <span>Open in Rocket League</span>
                    <ArrowTopRightOnSquareIcon className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Metadata */}
          <div className="text-xs text-gray-500 pt-4 border-t border-gray-200">
            <div className="flex justify-between">
              <span>User ID: {data.user_id}</span>
              <span>Generated: {new Date(data.generation_time).toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TrainingRecommendations;
