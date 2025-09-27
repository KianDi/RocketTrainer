import React from 'react';
import { CoachingInsights } from '../types';
import OverallPerformanceCard from './OverallPerformanceCard';
import PerformanceAreasGrid from './PerformanceAreasGrid';
import WeaknessAnalysisCard from './WeaknessAnalysisCard';
import StrengthsHighlight from './StrengthsHighlight';

interface CoachingInsightsSectionProps {
  insights: CoachingInsights;
  isLoading?: boolean;
}

const CoachingInsightsSection: React.FC<CoachingInsightsSectionProps> = ({ 
  insights, 
  isLoading = false 
}) => {
  if (isLoading) {
    return (
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
            <div className="h-40 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Section Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg shadow-md p-6 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold mb-2">🤖 AI Coaching Insights</h2>
            <p className="text-blue-100">
              Personalized analysis and recommendations based on your gameplay
            </p>
          </div>
          <div className="text-right">
            <div className="text-sm text-blue-200">Confidence Score</div>
            <div className="text-2xl font-bold">
              {Math.round(insights.confidence_score * 100)}%
            </div>
          </div>
        </div>
      </div>

      {/* Overall Performance */}
      <OverallPerformanceCard 
        score={insights.overall_performance_score}
        improvementPriority={insights.improvement_priority}
        keyTakeaway={insights.key_takeaway}
      />

      {/* Performance Areas Grid */}
      <PerformanceAreasGrid performanceAreas={insights.performance_areas} />

      {/* Weaknesses and Strengths */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weaknesses */}
        {insights.top_weaknesses.length > 0 && (
          <WeaknessAnalysisCard weaknesses={insights.top_weaknesses} />
        )}

        {/* Strengths */}
        {insights.top_strengths.length > 0 && (
          <StrengthsHighlight strengths={insights.top_strengths} />
        )}
      </div>

      {/* Insights Footer */}
      <div className="bg-gray-50 rounded-lg p-4 text-center text-sm text-gray-600">
        <p>
          Analysis generated on {new Date(insights.generated_at).toLocaleDateString()} • 
          Based on {insights.performance_areas.length} performance areas • 
          {insights.top_weaknesses.length} improvement opportunities identified
        </p>
      </div>
    </div>
  );
};

export default CoachingInsightsSection;
