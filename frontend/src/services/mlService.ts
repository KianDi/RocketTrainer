import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  WeaknessAnalysisRequest,
  WeaknessAnalysisResponse,
  TrainingRecommendationRequest,
  TrainingRecommendationResponse,
  ModelStatusResponse,
  MLApiError,
  RateLimitError
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * ML API Service for RocketTrainer
 * 
 * Provides methods to interact with the ML API endpoints including:
 * - Weakness analysis
 * - Training recommendations
 * - Model status monitoring
 * 
 * Includes comprehensive error handling, rate limiting support,
 * and loading state management.
 */
class MLService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: `${API_BASE_URL}/api/ml`,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 second timeout for ML operations
    });

    // Add response interceptor for error handling
    this.api.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        return Promise.reject(this.handleApiError(error));
      }
    );
  }

  /**
   * Handle API errors and convert them to user-friendly formats
   */
  private handleApiError(error: AxiosError): MLApiError | RateLimitError {
    if (error.response) {
      const { status, data } = error.response;
      
      // Handle rate limiting errors
      if (status === 429) {
        const rateLimitData = data as any;
        return {
          error: 'Rate Limit Exceeded',
          message: rateLimitData.detail?.message || 'Too many requests. Please try again later.',
          limit: rateLimitData.detail?.limit || 0,
          remaining: rateLimitData.detail?.remaining || 0,
          reset_time: rateLimitData.detail?.reset_time || 0,
          retry_after: rateLimitData.detail?.retry_after,
          timestamp: new Date().toISOString(),
        } as RateLimitError;
      }

      // Handle other API errors
      const apiError = data as any;
      return {
        error: `API Error (${status})`,
        message: apiError.detail || apiError.message || 'An unexpected error occurred',
        details: apiError,
        timestamp: new Date().toISOString(),
      };
    }

    // Handle network errors
    if (error.request) {
      return {
        error: 'Network Error',
        message: 'Unable to connect to the ML API. Please check your connection.',
        timestamp: new Date().toISOString(),
      };
    }

    // Handle other errors
    return {
      error: 'Unknown Error',
      message: error.message || 'An unexpected error occurred',
      timestamp: new Date().toISOString(),
    };
  }

  /**
   * Create an authenticated API instance with user token
   */
  createAuthenticatedApi(token: string): AxiosInstance {
    return axios.create({
      baseURL: `${API_BASE_URL}/api/ml`,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      timeout: 30000,
    });
  }

  /**
   * Analyze player weaknesses using ML models
   */
  async analyzeWeaknesses(
    request: WeaknessAnalysisRequest,
    token?: string
  ): Promise<WeaknessAnalysisResponse> {
    const api = token ? this.createAuthenticatedApi(token) : this.api;
    
    const response = await api.post<WeaknessAnalysisResponse>(
      '/analyze-weaknesses',
      request
    );
    
    return response.data;
  }

  /**
   * Get personalized training recommendations
   */
  async getTrainingRecommendations(
    request: TrainingRecommendationRequest,
    token?: string
  ): Promise<TrainingRecommendationResponse> {
    const api = token ? this.createAuthenticatedApi(token) : this.api;
    
    const response = await api.post<TrainingRecommendationResponse>(
      '/recommend-training',
      request
    );
    
    return response.data;
  }

  /**
   * Get ML model status and health information
   */
  async getModelStatus(token?: string): Promise<ModelStatusResponse> {
    const api = token ? this.createAuthenticatedApi(token) : this.api;
    
    const response = await api.get<ModelStatusResponse>('/model-status');
    
    return response.data;
  }

  /**
   * Check if the ML API is healthy and responsive
   */
  async healthCheck(token?: string): Promise<boolean> {
    try {
      const status = await this.getModelStatus(token);
      return status.system_status === 'healthy';
    } catch (error) {
      console.error('ML API health check failed:', error);
      return false;
    }
  }

  /**
   * Get rate limit information for debugging
   */
  getRateLimitInfo(error: any): RateLimitError | null {
    if (error && 'limit' in error && 'remaining' in error) {
      return error as RateLimitError;
    }
    return null;
  }

  /**
   * Format time until rate limit reset
   */
  formatRetryAfter(retryAfter: number): string {
    if (retryAfter < 60) {
      return `${retryAfter} seconds`;
    } else if (retryAfter < 3600) {
      return `${Math.ceil(retryAfter / 60)} minutes`;
    } else {
      return `${Math.ceil(retryAfter / 3600)} hours`;
    }
  }

  /**
   * Check if an error is a rate limit error
   */
  isRateLimitError(error: any): error is RateLimitError {
    return error && error.error === 'Rate Limit Exceeded';
  }

  /**
   * Check if an error is a network error
   */
  isNetworkError(error: any): boolean {
    return error && error.error === 'Network Error';
  }

  /**
   * Get user-friendly error message
   */
  getErrorMessage(error: any): string {
    if (this.isRateLimitError(error)) {
      const retryTime = error.retry_after ? this.formatRetryAfter(error.retry_after) : 'later';
      return `Rate limit exceeded. Please try again in ${retryTime}.`;
    }

    if (this.isNetworkError(error)) {
      return 'Unable to connect to the AI analysis service. Please check your connection and try again.';
    }

    return error.message || 'An unexpected error occurred. Please try again.';
  }

  /**
   * Get error severity level for UI display
   */
  getErrorSeverity(error: any): 'error' | 'warning' | 'info' {
    if (this.isRateLimitError(error)) {
      return 'warning';
    }

    if (this.isNetworkError(error)) {
      return 'error';
    }

    return 'error';
  }
}

export const mlService = new MLService();
export default mlService;
