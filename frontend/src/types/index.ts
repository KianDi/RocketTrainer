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
