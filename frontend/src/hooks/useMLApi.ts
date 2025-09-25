import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { mlService } from '../services/mlService';
import {
  WeaknessAnalysisRequest,
  WeaknessAnalysisResponse,
  TrainingRecommendationRequest,
  TrainingRecommendationResponse,
  ModelStatusResponse,
  MLApiError,
  RateLimitError
} from '../types';

/**
 * Hook for weakness analysis operations
 */
export const useWeaknessAnalysis = () => {
  const { user, token } = useAuth();
  const [data, setData] = useState<WeaknessAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<MLApiError | RateLimitError | null>(null);

  const analyzeWeaknesses = useCallback(async (
    request: Omit<WeaknessAnalysisRequest, 'user_id'>
  ) => {
    if (!user) {
      setError({
        error: 'Authentication Required',
        message: 'Please log in to analyze your weaknesses.',
        timestamp: new Date().toISOString(),
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fullRequest: WeaknessAnalysisRequest = {
        ...request,
        user_id: user.id,
      };

      const result = await mlService.analyzeWeaknesses(fullRequest, token || undefined);
      setData(result);
    } catch (err) {
      setError(err as MLApiError | RateLimitError);
    } finally {
      setLoading(false);
    }
  }, [user, token]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearData = useCallback(() => {
    setData(null);
  }, []);

  return {
    data,
    loading,
    error,
    analyzeWeaknesses,
    clearError,
    clearData,
    isRateLimited: error ? mlService.isRateLimitError(error) : false,
  };
};

/**
 * Hook for training recommendation operations
 */
export const useTrainingRecommendations = () => {
  const { user, token } = useAuth();
  const [data, setData] = useState<TrainingRecommendationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<MLApiError | RateLimitError | null>(null);

  const getRecommendations = useCallback(async (
    request: Omit<TrainingRecommendationRequest, 'user_id'>
  ) => {
    if (!user) {
      setError({
        error: 'Authentication Required',
        message: 'Please log in to get training recommendations.',
        timestamp: new Date().toISOString(),
      });
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const fullRequest: TrainingRecommendationRequest = {
        ...request,
        user_id: user.id,
      };

      const result = await mlService.getTrainingRecommendations(fullRequest, token || undefined);
      setData(result);
    } catch (err) {
      setError(err as MLApiError | RateLimitError);
    } finally {
      setLoading(false);
    }
  }, [user, token]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const clearData = useCallback(() => {
    setData(null);
  }, []);

  return {
    data,
    loading,
    error,
    getRecommendations,
    clearError,
    clearData,
    isRateLimited: error ? mlService.isRateLimitError(error) : false,
  };
};

/**
 * Hook for ML model status monitoring
 */
export const useModelStatus = (autoRefresh = false, refreshInterval = 30000) => {
  const { token } = useAuth();
  const [data, setData] = useState<ModelStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<MLApiError | null>(null);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const result = await mlService.getModelStatus(token || undefined);
      setData(result);
    } catch (err) {
      setError(err as MLApiError);
    } finally {
      setLoading(false);
    }
  }, [token]);

  // Auto-refresh functionality
  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(fetchStatus, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval, fetchStatus]);

  // Initial fetch
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    data,
    loading,
    error,
    fetchStatus,
    clearError,
    isHealthy: data?.system_status === 'healthy',
  };
};

/**
 * Combined hook for ML operations with shared state
 */
export const useMLOperations = () => {
  const weaknessAnalysis = useWeaknessAnalysis();
  const trainingRecommendations = useTrainingRecommendations();
  const modelStatus = useModelStatus();

  const isAnyLoading = weaknessAnalysis.loading || 
                      trainingRecommendations.loading || 
                      modelStatus.loading;

  const hasAnyError = weaknessAnalysis.error || 
                      trainingRecommendations.error || 
                      modelStatus.error;

  const clearAllErrors = useCallback(() => {
    weaknessAnalysis.clearError();
    trainingRecommendations.clearError();
    modelStatus.clearError();
  }, [weaknessAnalysis, trainingRecommendations, modelStatus]);

  const clearAllData = useCallback(() => {
    weaknessAnalysis.clearData();
    trainingRecommendations.clearData();
  }, [weaknessAnalysis, trainingRecommendations]);

  return {
    weaknessAnalysis,
    trainingRecommendations,
    modelStatus,
    isAnyLoading,
    hasAnyError,
    clearAllErrors,
    clearAllData,
  };
};

/**
 * Hook for ML API health monitoring
 */
export const useMLHealth = (checkInterval = 60000) => {
  const { token } = useAuth();
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const checkHealth = useCallback(async () => {
    try {
      const healthy = await mlService.healthCheck(token || undefined);
      setIsHealthy(healthy);
      setLastCheck(new Date());
    } catch (error) {
      setIsHealthy(false);
      setLastCheck(new Date());
    }
  }, [token]);

  useEffect(() => {
    // Initial health check
    checkHealth();

    // Set up periodic health checks
    const interval = setInterval(checkHealth, checkInterval);
    return () => clearInterval(interval);
  }, [checkHealth, checkInterval]);

  return {
    isHealthy,
    lastCheck,
    checkHealth,
  };
};
