import axios from 'axios';
import { getAuthToken } from './authService';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export interface ReplayResponse {
  id: string;
  filename?: string;
  ballchasing_id?: string;
  status: 'processing' | 'processed' | 'failed';
  message?: string;
  playlist?: string;
  result?: string;
  uploaded_at: string;
  processed_at?: string;
  task_id?: string;
}

export interface TaskStatus {
  task_id: string;
  state: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE';
  current: number;
  total: number;
  status: string;
  result?: any;
  error?: string;
}

export interface ReplayAnalysis {
  id: string;
  filename?: string;
  ballchasing_id?: string;
  playlist: string;
  duration: number;
  match_date?: string;
  result: string;
  score: string;
  player_stats: {
    goals?: number;
    assists?: number;
    saves?: number;
    shots?: number;
    score?: number;
    boost_usage?: number;
    average_speed?: number;
    time_supersonic?: number;
    time_on_ground?: number;
    time_low_air?: number;
    time_high_air?: number;
  };
  weakness_analysis?: any;
  processed: boolean;
  processed_at?: string;
  created_at: string;
}

class ReplayService {
  private getAuthHeaders() {
    const token = getAuthToken();
    return {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  private getUploadHeaders() {
    const token = getAuthToken();
    return {
      'Authorization': `Bearer ${token}`
      // Don't set Content-Type for file uploads - let browser set it
    };
  }

  async uploadReplay(file: File): Promise<ReplayResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(
        `${API_BASE_URL}/replays/upload`,
        formData,
        {
          headers: this.getUploadHeaders(),
          timeout: 60000, // 60 second timeout for uploads
        }
      );

      return response.data;
    } catch (error) {
      console.error('Upload replay failed:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Upload failed');
      }
      throw error;
    }
  }

  async getTaskStatus(taskId: string): Promise<TaskStatus> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/replays/task-status/${taskId}`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );

      return response.data;
    } catch (error) {
      console.error('Get task status failed:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to get task status');
      }
      throw error;
    }
  }

  async getUserReplays(skip: number = 0, limit: number = 20): Promise<ReplayResponse[]> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/replays/`,
        {
          headers: this.getAuthHeaders(),
          params: { skip, limit },
          timeout: 10000
        }
      );

      return response.data;
    } catch (error) {
      console.error('Get user replays failed:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to get replays');
      }
      throw error;
    }
  }

  async getReplayAnalysis(replayId: string): Promise<ReplayAnalysis> {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/replays/${replayId}/analysis`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );

      return response.data;
    } catch (error) {
      console.error('Get replay analysis failed:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to get replay analysis');
      }
      throw error;
    }
  }

  async deleteReplay(replayId: string): Promise<void> {
    try {
      await axios.delete(
        `${API_BASE_URL}/replays/${replayId}`,
        {
          headers: this.getAuthHeaders(),
          timeout: 10000
        }
      );
    } catch (error) {
      console.error('Delete replay failed:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Failed to delete replay');
      }
      throw error;
    }
  }

  async importFromBallchasing(ballchasingId: string): Promise<ReplayResponse> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/replays/ballchasing-import`,
        { ballchasing_id: ballchasingId },
        {
          headers: this.getAuthHeaders(),
          timeout: 30000
        }
      );

      return response.data;
    } catch (error) {
      console.error('Import from Ballchasing failed:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Import failed');
      }
      throw error;
    }
  }

  async searchBallchasingReplays(params: {
    player_name?: string;
    playlist?: string;
    season?: string;
    count?: number;
    sort_by?: string;
    sort_dir?: string;
  }): Promise<any> {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/replays/search-ballchasing`,
        params,
        {
          headers: this.getAuthHeaders(),
          timeout: 15000
        }
      );

      return response.data;
    } catch (error) {
      console.error('Search Ballchasing replays failed:', error);
      if (axios.isAxiosError(error)) {
        throw new Error(error.response?.data?.detail || 'Search failed');
      }
      throw error;
    }
  }
}

export const replayService = new ReplayService();
