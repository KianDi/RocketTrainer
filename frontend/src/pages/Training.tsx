import React, { useState } from 'react';
import { ChartBarIcon } from '@heroicons/react/24/outline';
import WeaknessAnalysis from '../components/WeaknessAnalysis';
import TrainingRecommendations from '../components/TrainingRecommendations';
import MLErrorBoundary from '../components/MLErrorBoundary';

const Training: React.FC = () => {
  const [weaknessAnalysisData, setWeaknessAnalysisData] = useState<any>(null);
  const [showAnalysis, setShowAnalysis] = useState(false);

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-3xl font-gaming font-bold text-gray-900">
            AI-Powered Training
          </h1>
          <p className="text-gray-600 mt-2">
            Get personalized training recommendations based on AI analysis of your gameplay
          </p>
        </div>

        {/* Action Buttons */}
        <div className="mb-8 flex space-x-4">
          <button
            onClick={() => setShowAnalysis(!showAnalysis)}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              showAnalysis
                ? 'bg-rl-blue text-white'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            <ChartBarIcon className="w-5 h-5" />
            <span>{showAnalysis ? 'Hide Analysis' : 'Show Weakness Analysis'}</span>
          </button>
        </div>

        {/* Weakness Analysis */}
        {showAnalysis && (
          <MLErrorBoundary>
            <WeaknessAnalysis
              onAnalysisComplete={setWeaknessAnalysisData}
              className="mb-8"
            />
          </MLErrorBoundary>
        )}

        {/* Training Recommendations */}
        <MLErrorBoundary>
          <TrainingRecommendations
            weaknessAnalysis={weaknessAnalysisData}
          />
        </MLErrorBoundary>
      </div>
    </div>
  );
};

export default Training;
