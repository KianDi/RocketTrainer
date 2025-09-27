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

export interface PlayerStats {
  // Core performance stats
  goals?: number;
  assists?: number;
  saves?: number;
  shots?: number;
  score?: number;

  // Movement and positioning metrics
  boost_usage?: number;
  average_speed?: number;
  time_supersonic?: number;
  time_on_ground?: number;
  time_low_air?: number;
  time_high_air?: number;

  // AI analysis scores (0-1 scale representing efficiency/performance)
  positioning_score?: number;
  rotation_score?: number;
  aerial_efficiency?: number;
  boost_efficiency?: number;

  // Action counts
  defensive_actions?: number;
  offensive_actions?: number;
}

export interface WeaknessAnalysis {
  primary_weakness?: string;
  confidence?: number;
  recommendations?: string[];
}

// New AI-powered coaching insights interfaces
export interface PerformanceArea {
  name: string;
  score: number;
  percentile?: number;
  status: 'strength' | 'average' | 'weakness';
  contributing_metrics: string[];
  raw_score?: number;
}

export interface WeaknessInsight {
  area: string;
  severity: number;
  impact_potential: number;
  primary_issue: string;
  coaching_feedback: string;
  specific_recommendations: string[];
  confidence: number;
}

export interface StrengthInsight {
  area: string;
  score: number;
  percentile?: number;
  positive_feedback: string;
  leverage_suggestions: string[];
}

export interface CoachingInsights {
  match_id: string;
  overall_performance_score: number;
  performance_areas: PerformanceArea[];
  top_weaknesses: WeaknessInsight[];
  top_strengths: StrengthInsight[];
  improvement_priority: string;
  key_takeaway: string;
  generated_at: string;
  confidence_score: number;
}

export interface CoachingInsightsResponse {
  success: boolean;
  insights?: CoachingInsights;
  error_message?: string;
  processing_time_ms?: number;
  cache_hit: boolean;
}

export interface ReplayAnalysis {
  id: string;
  filename?: string;
  ballchasing_id?: string;
  playlist: string;
  duration: number;
  match_date?: string;
  result: 'win' | 'loss' | 'tie';
  score: string; // Format: "1-2"
  player_stats: PlayerStats;
  weakness_analysis?: WeaknessAnalysis;
  processed: boolean;
  processed_at?: string;
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
  code: string;
  category: string;
  difficulty: number; // 1-5 scale
  relevance_score: number;
  difficulty_match: number;
  quality_score: number;
  overall_score: number;
  reasoning: string;
  estimated_improvement?: number;
}

export interface TrainingRecommendationResponse {
  user_id: string;
  recommendations: TrainingRecommendationItem[];
  skill_level_detected: string;
  total_packs_evaluated: number;
  generation_time: string;
  cache_hit: boolean;
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
