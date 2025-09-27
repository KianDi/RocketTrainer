import React, { useState } from 'react';
import { StrengthInsight } from '../types';

interface StrengthsHighlightProps {
  strengths: StrengthInsight[];
}

const StrengthsHighlight: React.FC<StrengthsHighlightProps> = ({ strengths }) => {
  const [expandedStrength, setExpandedStrength] = useState<number | null>(null);

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
        return '⭐';
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

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-semibold text-gray-800">⭐ Your Strengths</h3>
        <span className="text-sm text-gray-500">
          {strengths.length} strength{strengths.length !== 1 ? 's' : ''} identified
        </span>
      </div>

      <div className="space-y-4">
        {strengths.map((strength, index) => (
          <div
            key={index}
            className="border border-green-200 bg-green-50 rounded-lg p-4 transition-all hover:shadow-md"
          >
            {/* Strength Header */}
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedStrength(expandedStrength === index ? null : index)}
            >
              <div className="flex items-center space-x-3">
                <span className="text-xl">{getAreaIcon(strength.area)}</span>
                <div>
                  <h4 className="font-semibold text-green-800">
                    {getAreaDisplayName(strength.area)}
                  </h4>
                  <p className="text-sm text-green-600">
                    Score: {Math.round(strength.score * 100)}/100
                    {strength.percentile && ` (${Math.round(strength.percentile)}th percentile)`}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="text-right">
                  <div className="text-xs font-medium text-green-700">Strength</div>
                  <div className="text-xs text-green-600">
                    Keep it up!
                  </div>
                </div>
                <svg
                  className={`w-5 h-5 text-green-600 transition-transform ${
                    expandedStrength === index ? 'rotate-180' : ''
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
            {expandedStrength === index && (
              <div className="mt-4 pt-4 border-t border-green-200 space-y-4">
                {/* Positive Feedback */}
                <div>
                  <h5 className="font-medium text-green-700 mb-2">🎉 What You're Doing Well</h5>
                  <p className="text-green-700 bg-white p-3 rounded border border-green-200">
                    {strength.positive_feedback}
                  </p>
                </div>

                {/* Leverage Suggestions */}
                {strength.leverage_suggestions.length > 0 && (
                  <div>
                    <h5 className="font-medium text-green-700 mb-2">🚀 How to Leverage This Strength</h5>
                    <ul className="space-y-2">
                      {strength.leverage_suggestions.map((suggestion, sugIndex) => (
                        <li key={sugIndex} className="flex items-start space-x-2">
                          <span className="text-green-500 mt-1">💡</span>
                          <span className="text-green-700 text-sm">{suggestion}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {strengths.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <span className="text-4xl mb-2 block">🔍</span>
          <p>No standout strengths identified yet.</p>
          <p className="text-sm">Keep playing to build your strengths!</p>
        </div>
      )}
    </div>
  );
};

export default StrengthsHighlight;
