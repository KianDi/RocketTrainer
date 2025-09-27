import React from 'react';

interface OverallPerformanceCardProps {
  score: number;
  improvementPriority: string;
  keyTakeaway: string;
}

const OverallPerformanceCard: React.FC<OverallPerformanceCardProps> = ({
  score,
  improvementPriority,
  keyTakeaway
}) => {
  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600';
    if (score >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score: number) => {
    if (score >= 0.8) return 'Excellent';
    if (score >= 0.7) return 'Good';
    if (score >= 0.6) return 'Average';
    if (score >= 0.4) return 'Below Average';
    return 'Needs Improvement';
  };

  const getProgressBarColor = (score: number) => {
    if (score >= 0.8) return 'bg-green-500';
    if (score >= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold mb-4 text-gray-800">Overall Performance</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Performance Score */}
        <div className="text-center">
          <div className="relative w-24 h-24 mx-auto mb-3">
            {/* Circular Progress */}
            <svg className="w-24 h-24 transform -rotate-90" viewBox="0 0 100 100">
              <circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                className="text-gray-200"
              />
              <circle
                cx="50"
                cy="50"
                r="40"
                stroke="currentColor"
                strokeWidth="8"
                fill="transparent"
                strokeDasharray={`${2 * Math.PI * 40}`}
                strokeDashoffset={`${2 * Math.PI * 40 * (1 - score)}`}
                className={getProgressBarColor(score).replace('bg-', 'text-')}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className={`text-2xl font-bold ${getScoreColor(score)}`}>
                {Math.round(score * 100)}
              </span>
            </div>
          </div>
          <div className="text-sm text-gray-600">Performance Score</div>
          <div className={`font-semibold ${getScoreColor(score)}`}>
            {getScoreLabel(score)}
          </div>
        </div>

        {/* Improvement Priority */}
        <div className="md:col-span-2 space-y-4">
          <div>
            <h4 className="font-semibold text-gray-700 mb-2">🎯 Priority Focus Area</h4>
            <p className="text-gray-600 bg-blue-50 p-3 rounded-lg border-l-4 border-blue-400">
              {improvementPriority}
            </p>
          </div>

          {keyTakeaway && (
            <div>
              <h4 className="font-semibold text-gray-700 mb-2">💡 Key Takeaway</h4>
              <p className="text-gray-600 bg-yellow-50 p-3 rounded-lg border-l-4 border-yellow-400">
                {keyTakeaway}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OverallPerformanceCard;
