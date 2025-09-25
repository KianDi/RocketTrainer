import React from 'react';
import { 
  CpuChipIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
  ArrowPathIcon
} from '@heroicons/react/24/outline';
import { useModelStatus } from '../hooks/useMLApi';
import { ModelInfo } from '../types';

interface MLSystemStatusProps {
  autoRefresh?: boolean;
  refreshInterval?: number;
  className?: string;
}

const MLSystemStatus: React.FC<MLSystemStatusProps> = ({ 
  autoRefresh = true,
  refreshInterval = 30000,
  className = '' 
}) => {
  const { data, loading, error, fetchStatus } = useModelStatus(autoRefresh, refreshInterval);

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'ready':
        return <CheckCircleIcon className="w-5 h-5 text-green-500" />;
      case 'warning':
      case 'degraded':
        return <ExclamationTriangleIcon className="w-5 h-5 text-yellow-500" />;
      case 'error':
      case 'unhealthy':
        return <XCircleIcon className="w-5 h-5 text-red-500" />;
      default:
        return <ClockIcon className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string): string => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'ready':
        return 'text-green-600 bg-green-100';
      case 'warning':
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
      case 'unhealthy':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatUptime = (seconds: number): string => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  const formatNumber = (num: number): string => {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  };

  if (error) {
    return (
      <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">ML System Status</h2>
          <button
            onClick={fetchStatus}
            className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
          >
            <ArrowPathIcon className="w-5 h-5" />
          </button>
        </div>
        
        <div className="text-center py-8">
          <XCircleIcon className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Unable to Load Status</h3>
          <p className="text-gray-600 mb-4">Failed to connect to the ML system monitoring.</p>
          <button onClick={fetchStatus} className="btn-primary">
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <CpuChipIcon className="w-6 h-6 text-rl-blue" />
          <h2 className="text-xl font-bold text-gray-900">ML System Status</h2>
        </div>
        
        <div className="flex items-center space-x-3">
          {data && (
            <div className="flex items-center space-x-2">
              {getStatusIcon(data.system_status)}
              <span className={`px-2 py-1 rounded-full text-sm font-medium ${getStatusColor(data.system_status)}`}>
                {data.system_status.charAt(0).toUpperCase() + data.system_status.slice(1)}
              </span>
            </div>
          )}
          
          <button
            onClick={fetchStatus}
            disabled={loading}
            className="p-2 text-gray-500 hover:text-gray-700 rounded-lg hover:bg-gray-100"
          >
            <ArrowPathIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {data && (
        <div className="space-y-6">
          {/* System Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {formatUptime(data.uptime)}
              </div>
              <div className="text-sm text-gray-600">Uptime</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {data.memory_usage.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Memory Usage</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {data.models.length}
              </div>
              <div className="text-sm text-gray-600">ML Models</div>
            </div>
            
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">
                {data.cache_stats.hit_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">Cache Hit Rate</div>
            </div>
          </div>

          {/* ML Models Status */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">ML Models</h3>
            <div className="space-y-3">
              {data.models.map((model: ModelInfo, index: number) => (
                <div key={index} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(model.status)}
                    <div>
                      <div className="font-medium text-gray-900">{model.name}</div>
                      <div className="text-sm text-gray-600">v{model.version}</div>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm text-gray-900">
                      {formatNumber(model.predictions_served)} predictions
                    </div>
                    <div className="text-sm text-gray-600">
                      {model.avg_response_time.toFixed(1)}ms avg
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Cache Statistics */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Cache Performance</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-blue-50 rounded-lg">
                <div className="text-lg font-bold text-blue-900">
                  {formatNumber(data.cache_stats.total_requests)}
                </div>
                <div className="text-xs text-blue-600">Total Requests</div>
              </div>
              
              <div className="text-center p-3 bg-green-50 rounded-lg">
                <div className="text-lg font-bold text-green-900">
                  {formatNumber(data.cache_stats.cache_hits)}
                </div>
                <div className="text-xs text-green-600">Cache Hits</div>
              </div>
              
              <div className="text-center p-3 bg-red-50 rounded-lg">
                <div className="text-lg font-bold text-red-900">
                  {formatNumber(data.cache_stats.cache_misses)}
                </div>
                <div className="text-xs text-red-600">Cache Misses</div>
              </div>
              
              <div className="text-center p-3 bg-purple-50 rounded-lg">
                <div className="text-lg font-bold text-purple-900">
                  {data.cache_stats.avg_cache_time.toFixed(1)}ms
                </div>
                <div className="text-xs text-purple-600">Avg Cache Time</div>
              </div>
            </div>
          </div>

          {/* Rate Limiting */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Rate Limiting</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {data.rate_limit_stats.total_tracked_users}
                </div>
                <div className="text-xs text-gray-600">Tracked Users</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {data.rate_limit_stats.total_rate_limit_keys}
                </div>
                <div className="text-xs text-gray-600">Rate Limit Keys</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className={`text-lg font-bold ${data.rate_limit_stats.rate_limiter_healthy ? 'text-green-900' : 'text-red-900'}`}>
                  {data.rate_limit_stats.rate_limiter_healthy ? 'Healthy' : 'Unhealthy'}
                </div>
                <div className="text-xs text-gray-600">Rate Limiter</div>
              </div>
            </div>
            
            {Object.keys(data.rate_limit_stats.endpoints).length > 0 && (
              <div className="mt-3">
                <div className="text-sm font-medium text-gray-700 mb-2">Endpoint Usage:</div>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(data.rate_limit_stats.endpoints).map(([endpoint, count]) => (
                    <span key={endpoint} className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                      {endpoint}: {count}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Database Pool */}
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Database Pool</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {data.database_pool.pool_size}
                </div>
                <div className="text-xs text-gray-600">Pool Size</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {data.database_pool.checked_out_connections}
                </div>
                <div className="text-xs text-gray-600">Active</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {data.database_pool.checked_in_connections}
                </div>
                <div className="text-xs text-gray-600">Available</div>
              </div>
              
              <div className="text-center p-3 bg-gray-50 rounded-lg">
                <div className="text-lg font-bold text-gray-900">
                  {data.database_pool.utilization_percent.toFixed(1)}%
                </div>
                <div className="text-xs text-gray-600">Utilization</div>
              </div>
            </div>
          </div>

          {/* Last Updated */}
          <div className="text-xs text-gray-500 pt-4 border-t border-gray-200 text-center">
            Last updated: {new Date(data.last_health_check).toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
};

export default MLSystemStatus;
