/**
 * Auth API client for Google OAuth and user management.
 */

import axios from 'axios';

const API_BASE = '/api';

// ============================================================================
// Types
// ============================================================================

export interface User {
  id: number;
  email: string;
  name: string;
  picture_url?: string;
}

export interface AuthStatus {
  authenticated: boolean;
  user: User | null;
  oauth_configured: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// ============================================================================
// Token Management
// ============================================================================

const TOKEN_KEY = 'auth_token';

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

// ============================================================================
// Axios Interceptor Setup
// ============================================================================

export function setupAuthInterceptor(): void {
  axios.interceptors.request.use(
    (config) => {
      const token = getStoredToken();
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => Promise.reject(error)
  );

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        clearStoredToken();
        // Optionally trigger a re-render or redirect
        window.dispatchEvent(new CustomEvent('auth:logout'));
      }
      return Promise.reject(error);
    }
  );
}

// ============================================================================
// Auth API Functions
// ============================================================================

/**
 * Get current authentication status.
 */
export async function getAuthStatus(): Promise<AuthStatus> {
  const response = await axios.get<AuthStatus>(`${API_BASE}/auth/status`);
  return response.data;
}

/**
 * Get the Google login URL and redirect.
 */
export function loginWithGoogle(): void {
  window.location.href = `${API_BASE}/auth/login/google`;
}

/**
 * Get current user info (requires authentication).
 */
export async function getCurrentUser(): Promise<User> {
  const response = await axios.get<User>(`${API_BASE}/auth/me`);
  return response.data;
}

/**
 * Logout the current user.
 */
export async function logout(): Promise<void> {
  try {
    await axios.post(`${API_BASE}/auth/logout`);
  } finally {
    clearStoredToken();
  }
}

/**
 * Logout from all sessions.
 */
export async function logoutAll(): Promise<void> {
  try {
    await axios.post(`${API_BASE}/auth/logout-all`);
  } finally {
    clearStoredToken();
  }
}

/**
 * Handle OAuth callback - extract token from URL.
 * Call this on app load to check for OAuth redirect.
 */
export function handleOAuthCallback(): string | null {
  const params = new URLSearchParams(window.location.search);
  const token = params.get('token');
  const error = params.get('error');

  if (error) {
    console.error('OAuth error:', error);
    // Clean URL
    window.history.replaceState({}, '', window.location.pathname);
    return null;
  }

  if (token) {
    setStoredToken(token);
    // Clean URL
    window.history.replaceState({}, '', window.location.pathname);
    return token;
  }

  return getStoredToken();
}
