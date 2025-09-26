import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    steam_id?: string;
    epic_id?: string;
    current_rank?: string;
    is_premium: boolean;
  };
}

interface User {
  id: string;
  username: string;
  steam_id?: string;
  epic_id?: string;
  email?: string;
  current_rank?: string;
  mmr?: number;
  platform?: string;
  is_premium: boolean;
  created_at: string;
  last_login?: string;
}

class AuthService {
  private api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  async steamLogin(steamId: string, username?: string): Promise<LoginResponse> {
    const response = await this.api.post('/auth/steam-login', {
      steam_id: steamId,
      username: username,
    });
    return response.data;
  }

  async getCurrentUser(token: string): Promise<User> {
    const response = await this.api.get('/auth/me', {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  }

  async logout(token: string): Promise<void> {
    await this.api.post('/auth/logout', {}, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  // Helper method to create authenticated axios instance
  createAuthenticatedApi(token: string) {
    return axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
    });
  }
}

// Helper function to get auth token from localStorage
export const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

// Helper function to set auth token in localStorage
export const setAuthToken = (token: string): void => {
  localStorage.setItem('auth_token', token);
};

// Helper function to remove auth token from localStorage
export const removeAuthToken = (): void => {
  localStorage.removeItem('auth_token');
};

export const authService = new AuthService();
