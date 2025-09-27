import React from 'react';
import { PerformanceArea } from '../types';
import PerformanceAreaCard from './PerformanceAreaCard';

interface PerformanceAreasGridProps {
  performanceAreas: PerformanceArea[];
}

const PerformanceAreasGrid: React.FC<PerformanceAreasGridProps> = ({ performanceAreas }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-semibold mb-4 text-gray-800">Performance Breakdown</h3>
      <p className="text-gray-600 mb-6">
        Your performance across key gameplay areas. Each area is scored from 0-100 based on your gameplay metrics.
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
        {performanceAreas.map((area) => (
          <PerformanceAreaCard key={area.name} area={area} />
        ))}
      </div>
    </div>
  );
};

export default PerformanceAreasGrid;
