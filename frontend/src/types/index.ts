/**
 * TypeScript type definitions for RocketTrainer
 */

// User types
export interface User {
  id: string;
  steam_id: string;
  username: string;
  avatar_url?: string;
  rank?: string;
  created_at: string;
  updated_at: string;
}

// Authentication types
export interface LoginRequest {
  steam_id: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Replay types
export interface ReplayUpload {
  file: File;
}

export interface ReplayAnalysis {
  id: string;
  filename: string;
  status: 'processing' | 'completed' | 'failed';
  weaknesses: string[];
  recommendations: TrainingRecommendation[];
  created_at: string;
}

// Training types
export interface TrainingPack {
  id: string;
  code: string;
  name: string;
  description: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced' | 'expert';
  category: string;
  tags: string[];
  created_at: string;
}

export interface TrainingRecommendation {
  training_pack: TrainingPack;
  reason: string;
  priority: number;
}

export interface TrainingSession {
  id: string;
  user_id: string;
  training_pack_id: string;
  duration_minutes: number;
  completed_shots: number;
  total_shots: number;
  accuracy_percentage: number;
  created_at: string;
}

// API Response types
export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface ApiError {
  detail: string;
  status_code: number;
}

// Component Props types
export interface ProtectedRouteProps {
  children: React.ReactNode;
}

export interface NavbarProps {
  user?: User;
  onLogout: () => void;
}

// ML API Types
export interface SkillCategoryScore {
  category: string;
  score: number;
  percentile?: number;
  trend?: string;
}

export interface WeaknessAnalysisRequest {
  user_id: string;
  match_ids?: string[];
  include_confidence?: boolean;
  analysis_depth?: 'quick' | 'standard' | 'detailed';
}

export interface WeaknessAnalysisResponse {
  user_id: string;
  analysis_date: string;
  primary_weakness: string;
  confidence: number;
  skill_categories: SkillCategoryScore[];
  matches_analyzed: number;
  recommendations_available: boolean;
  analysis_summary?: string;
}

export interface TrainingRecommendationRequest {
  user_id: string;
  skill_level?: string;
  max_recommendations?: number;
  focus_areas?: string[];
}

export interface TrainingRecommendationItem {
  training_pack_id: string;
  name: string;
  description: string;
  difficulty: string;
  category: string;
  code: string;
  creator: string;
  relevance_score: number;
  reasoning: string;
  estimated_improvement: number;
  time_investment: string;
}

export interface TrainingRecommendationResponse {
  user_id: string;
  recommendation_id: string;
  skill_level: string;
  recommendations: TrainingRecommendationItem[];
  total_recommendations: number;
  personalization_score: number;
  cache_hit: boolean;
  processing_time_ms: number;
  generated_at: string;
}

export interface ModelInfo {
  name: string;
  version: string;
  status: string;
  last_trained?: string;
  accuracy?: number;
  predictions_served: number;
  avg_response_time: number;
}

export interface CacheStatistics {
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  hit_rate: number;
  avg_cache_time: number;
}

export interface DatabasePoolStatistics {
  pool_size: number;
  checked_in_connections: number;
  checked_out_connections: number;
  overflow_connections: number;
  invalid_connections: number;
  total_connections: number;
  utilization_percent: number;
}

export interface RateLimitStatistics {
  total_tracked_users: number;
  total_rate_limit_keys: number;
  endpoints: Record<string, number>;
  rate_limiter_healthy: boolean;
}

export interface ModelStatusResponse {
  system_status: string;
  models: ModelInfo[];
  cache_stats: CacheStatistics;
  database_pool: DatabasePoolStatistics;
  rate_limit_stats: RateLimitStatistics;
  uptime: number;
  memory_usage: number;
  last_health_check: string;
}

// ML API Error Types
export interface MLApiError {
  error: string;
  message: string;
  details?: Record<string, any>;
  timestamp: string;
}

export interface RateLimitError extends MLApiError {
  limit: number;
  remaining: number;
  reset_time: number;
  retry_after?: number;
}
