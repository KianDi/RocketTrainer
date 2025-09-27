import React, { useState } from 'react';
import { WeaknessInsight } from '../types';

interface WeaknessAnalysisCardProps {
  weaknesses: WeaknessInsight[];
}

const WeaknessAnalysisCard: React.FC<WeaknessAnalysisCardProps> = ({ weaknesses }) => {
  const [expandedWeakness, setExpandedWeakness] = useState<number | null>(null);

  const getAreaIcon = (areaName: string) => {
    switch (areaName) {
      case 'positioning':
        return '📍';
      case 'rotation':
        return '🔄';
      case 'mechanics':
        return '⚙️';
      case 'game_sense':
        return '🧠';
      case 'boost_management':
        return '⚡';
      default:
        return '⚠️';
    }
  };

  const getAreaDisplayName = (areaName: string) => {
    switch (areaName) {
      case 'positioning':
        return 'Positioning';
      case 'rotation':
        return 'Rotation';
      case 'mechanics':
        return 'Mechanics';
      case 'game_sense':
        return 'Game Sense';
      case 'boost_management':
        return 'Boost Management';
      default:
        return areaName.charAt(0).toUpperCase() + areaName.slice(1);
    }
  };

  const getSeverityColor = (severity: number) => {
    if (severity >= 0.7) return 'text-red-600 bg-red-50 border-red-200';
    if (severity >= 0.4) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-yellow-600 bg-yellow-50 border-yellow-200';
  };

  const getSeverityLabel = (severity: number) => {
    if (severity >= 0.7) return 'High Priority';
    if (severity >= 0.4) return 'Medium Priority';
    return 'Low Priority';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-gray-800">🎯 Areas for Improvement</h3>
        <span className="text-sm text-gray-500">
          {weaknesses.length} area{weaknesses.length !== 1 ? 's' : ''} identified
        </span>
      </div>

      <div className="space-y-4">
        {weaknesses.map((weakness, index) => (
          <div
            key={index}
            className={`border rounded-lg p-4 transition-all ${getSeverityColor(weakness.severity)}`}
          >
            {/* Weakness Header */}
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedWeakness(expandedWeakness === index ? null : index)}
            >
              <div className="flex items-center space-x-3">
                <span className="text-xl">{getAreaIcon(weakness.area)}</span>
                <div>
                  <h4 className="font-semibold text-gray-800">
                    {getAreaDisplayName(weakness.area)}
                  </h4>
                  <p className="text-sm text-gray-600">{weakness.primary_issue}</p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-xs font-medium">
                    {getSeverityLabel(weakness.severity)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {Math.round(weakness.impact_potential * 100)}% improvement potential
                  </div>
                </div>
                <svg
                  className={`w-5 h-5 transition-transform ${
                    expandedWeakness === index ? 'rotate-180' : ''
                  }`}
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </div>
            </div>

            {/* Expanded Content */}
            {expandedWeakness === index && (
              <div className="mt-4 pt-4 border-t border-gray-200 space-y-4">
                {/* Coaching Feedback */}
                <div>
                  <h5 className="font-medium text-gray-700 mb-2">💬 Coaching Feedback</h5>
                  <p className="text-gray-600 bg-white p-3 rounded border">
                    {weakness.coaching_feedback}
                  </p>
                </div>

                {/* Specific Recommendations */}
                {weakness.specific_recommendations.length > 0 && (
                  <div>
                    <h5 className="font-medium text-gray-700 mb-2">📋 Action Items</h5>
                    <ul className="space-y-2">
                      {weakness.specific_recommendations.map((recommendation, recIndex) => (
                        <li key={recIndex} className="flex items-start space-x-2">
                          <span className="text-green-500 mt-1">✓</span>
                          <span className="text-gray-600 text-sm">{recommendation}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Confidence Score */}
                <div className="flex items-center justify-between text-sm text-gray-500">
                  <span>Analysis Confidence: {Math.round(weakness.confidence * 100)}%</span>
                  <span>Priority Score: {Math.round((weakness.severity * weakness.impact_potential) * 100)}</span>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {weaknesses.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <span className="text-4xl mb-2 block">🎉</span>
          <p>No significant weaknesses detected!</p>
          <p className="text-sm">Keep up the great work!</p>
        </div>
      )}
    </div>
  );
};

export default WeaknessAnalysisCard;
