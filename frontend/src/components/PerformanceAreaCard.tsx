import React from 'react';
import { PerformanceArea } from '../types';

interface PerformanceAreaCardProps {
  area: PerformanceArea;
}

const PerformanceAreaCard: React.FC<PerformanceAreaCardProps> = ({ area }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'strength':
        return {
          bg: 'bg-green-50',
          border: 'border-green-200',
          text: 'text-green-700',
          progress: 'bg-green-500'
        };
      case 'average':
        return {
          bg: 'bg-yellow-50',
          border: 'border-yellow-200',
          text: 'text-yellow-700',
          progress: 'bg-yellow-500'
        };
      case 'weakness':
        return {
          bg: 'bg-red-50',
          border: 'border-red-200',
          text: 'text-red-700',
          progress: 'bg-red-500'
        };
      default:
        return {
          bg: 'bg-gray-50',
          border: 'border-gray-200',
          text: 'text-gray-700',
          progress: 'bg-gray-500'
        };
    }
  };

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
        return '📊';
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

  const colors = getStatusColor(area.status);
  const score = Math.round(area.score * 100);

  return (
    <div className={`${colors.bg} ${colors.border} border rounded-lg p-4 transition-all hover:shadow-md`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getAreaIcon(area.name)}</span>
          <span className="font-medium text-gray-800 text-sm">
            {getAreaDisplayName(area.name)}
          </span>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full ${colors.bg} ${colors.text} font-medium`}>
          {area.status}
        </span>
      </div>

      {/* Score Circle */}
      <div className="flex justify-center mb-3">
        <div className="relative w-16 h-16">
          <svg className="w-16 h-16 transform -rotate-90" viewBox="0 0 100 100">
            <circle
              cx="50"
              cy="50"
              r="35"
              stroke="currentColor"
              strokeWidth="6"
              fill="transparent"
              className="text-gray-200"
            />
            <circle
              cx="50"
              cy="50"
              r="35"
              stroke="currentColor"
              strokeWidth="6"
              fill="transparent"
              strokeDasharray={`${2 * Math.PI * 35}`}
              strokeDashoffset={`${2 * Math.PI * 35 * (1 - area.score)}`}
              className={colors.progress.replace('bg-', 'text-')}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-lg font-bold ${colors.text}`}>
              {score}
            </span>
          </div>
        </div>
      </div>

      {/* Percentile (if available) */}
      {area.percentile && (
        <div className="text-center text-xs text-gray-600">
          {Math.round(area.percentile)}th percentile
        </div>
      )}

      {/* Contributing Metrics */}
      {area.contributing_metrics.length > 0 && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <div className="text-xs text-gray-500 mb-1">Based on:</div>
          <div className="flex flex-wrap gap-1">
            {area.contributing_metrics.slice(0, 3).map((metric, index) => (
              <span
                key={index}
                className="text-xs bg-white px-2 py-1 rounded text-gray-600"
              >
                {metric.replace(/_/g, ' ')}
              </span>
            ))}
            {area.contributing_metrics.length > 3 && (
              <span className="text-xs text-gray-400">
                +{area.contributing_metrics.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceAreaCard;
