import React, { useState } from 'react';
import { 
  ChartBarIcon, 
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useWeaknessAnalysis } from '../hooks/useMLApi';
import { mlService } from '../services/mlService';
import { SkillCategoryScore } from '../types';

interface WeaknessAnalysisProps {
  onAnalysisComplete?: (analysis: any) => void;
  className?: string;
}

const WeaknessAnalysis: React.FC<WeaknessAnalysisProps> = ({ 
  onAnalysisComplete, 
  className = '' 
}) => {
  const { data, loading, error, analyzeWeaknesses, clearError } = useWeaknessAnalysis();
  const [analysisDepth, setAnalysisDepth] = useState<'quick' | 'standard' | 'detailed'>('standard');

  const handleAnalyze = async () => {
    await analyzeWeaknesses({
      include_confidence: true,
      analysis_depth: analysisDepth,
    });
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-100';
    if (score >= 60) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getScoreBarColor = (score: number): string => {
    if (score >= 80) return 'bg-green-500';
    if (score >= 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const formatProcessingTime = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  React.useEffect(() => {
    if (data && onAnalysisComplete) {
      onAnalysisComplete(data);
    }
  }, [data, onAnalysisComplete]);

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <ChartBarIcon className="w-6 h-6 text-rl-blue" />
          <h2 className="text-xl font-bold text-gray-900">AI Weakness Analysis</h2>
        </div>
        
        {data && (
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <ClockIcon className="w-4 h-4" />
            <span>Processed in {formatProcessingTime(data.processing_time_ms)}</span>
            {data.cache_hit && (
              <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                Cached
              </span>
            )}
          </div>
        )}
      </div>

      {/* Analysis Controls */}
      <div className="mb-6">
        <div className="flex items-center space-x-4 mb-4">
          <label className="text-sm font-medium text-gray-700">Analysis Depth:</label>
          <select
            value={analysisDepth}
            onChange={(e) => setAnalysisDepth(e.target.value as any)}
            className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-rl-blue"
            disabled={loading}
          >
            <option value="quick">Quick (30s)</option>
            <option value="standard">Standard (60s)</option>
            <option value="detailed">Detailed (120s)</option>
          </select>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="btn-primary flex items-center space-x-2"
        >
          {loading ? (
            <>
              <ArrowPathIcon className="w-4 h-4 animate-spin" />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <ChartBarIcon className="w-4 h-4" />
              <span>Analyze My Gameplay</span>
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
                {mlService.isRateLimitError(error) ? 'Rate Limit Exceeded' : 'Analysis Failed'}
              </h3>
              <p className="text-sm text-red-700 mt-1">
                {mlService.getErrorMessage(error)}
              </p>
              {mlService.isRateLimitError(error) && error.retry_after && (
                <p className="text-xs text-red-600 mt-2">
                  You can try again in {mlService.formatRetryAfter(error.retry_after)}
                </p>
              )}
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

      {/* Analysis Results */}
      {data && (
        <div className="space-y-6">
          {/* Summary */}
          <div className="bg-gray-50 rounded-lg p-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">
                  {data.matches_analyzed}
                </div>
                <div className="text-sm text-gray-600">Matches Analyzed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-rl-blue">
                  {Math.round(data.confidence * 100)}%
                </div>
                <div className="text-sm text-gray-600">Confidence</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {Math.round(data.improvement_potential * 100)}%
                </div>
                <div className="text-sm text-gray-600">Improvement Potential</div>
              </div>
            </div>
          </div>

          {/* Primary Weaknesses */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Key Areas for Improvement</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                <div>
                  <span className="font-medium text-red-800">Primary: {data.primary_weakness}</span>
                  <div className="text-sm text-red-600">Highest priority for improvement</div>
                </div>
                <div className="px-3 py-1 bg-red-200 text-red-800 rounded-full text-sm font-medium">
                  #1
                </div>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div>
                  <span className="font-medium text-yellow-800">Secondary: {data.secondary_weakness}</span>
                  <div className="text-sm text-yellow-600">Second priority for improvement</div>
                </div>
                <div className="px-3 py-1 bg-yellow-200 text-yellow-800 rounded-full text-sm font-medium">
                  #2
                </div>
              </div>
            </div>
          </div>

          {/* Skill Scores */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Detailed Skill Breakdown</h3>
            <div className="space-y-3">
              {data.skill_scores.map((skill: SkillCategoryScore, index: number) => (
                <div key={index} className="p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">{skill.category}</span>
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-sm font-medium ${getScoreColor(skill.score)}`}>
                        {skill.score}/100
                      </span>
                      <span className="text-xs text-gray-500">
                        {Math.round(skill.confidence * 100)}% confidence
                      </span>
                    </div>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                    <div
                      className={`h-2 rounded-full transition-all duration-500 ${getScoreBarColor(skill.score)}`}
                      style={{ width: `${skill.score}%` }}
                    ></div>
                  </div>
                  
                  <p className="text-sm text-gray-600">{skill.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Recommendations */}
          {data.recommendations && data.recommendations.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-3">AI Recommendations</h3>
              <div className="space-y-2">
                {data.recommendations.map((recommendation: string, index: number) => (
                  <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                    <CheckCircleIcon className="w-5 h-5 text-blue-500 mt-0.5" />
                    <span className="text-sm text-blue-800">{recommendation}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Analysis Metadata */}
          <div className="text-xs text-gray-500 pt-4 border-t border-gray-200">
            <div className="flex justify-between">
              <span>Analysis ID: {data.analysis_id}</span>
              <span>Generated: {new Date(data.analysis_timestamp).toLocaleString()}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WeaknessAnalysis;
