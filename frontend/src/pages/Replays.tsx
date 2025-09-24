import React from 'react';

const Replays: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-gaming font-bold text-gray-900 mb-8">
          Replay Analysis
        </h1>
        
        <div className="card text-center py-12">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Coming Soon
          </h2>
          <p className="text-gray-600 mb-6">
            Upload and analyze your Rocket League replays to identify areas for improvement.
          </p>
          <button className="btn-primary">
            Upload Replay
          </button>
        </div>
      </div>
    </div>
  );
};

export default Replays;
