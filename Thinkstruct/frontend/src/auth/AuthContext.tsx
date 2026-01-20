/**
 * Auth Context Provider for managing authentication state.
 */

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from 'react';
import {
  type User,
  type AuthStatus,
  getAuthStatus,
  loginWithGoogle,
  logout as apiLogout,
  handleOAuthCallback,
  setupAuthInterceptor,
  clearStoredToken,
} from './authApi';

// ============================================================================
// Types
// ============================================================================

interface AuthContextValue {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  oauthConfigured: boolean;
  login: () => void;
  logout: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

// ============================================================================
// Context
// ============================================================================

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ============================================================================
// Provider Component
// ============================================================================

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [oauthConfigured, setOauthConfigured] = useState(false);

  const refreshAuth = useCallback(async () => {
    try {
      const status: AuthStatus = await getAuthStatus();
      setUser(status.user);
      setOauthConfigured(status.oauth_configured);
    } catch (error) {
      console.error('Failed to get auth status:', error);
      setUser(null);
    }
  }, []);

  // Initialize auth on mount
  useEffect(() => {
    setupAuthInterceptor();

    // Handle OAuth callback (check for token in URL)
    handleOAuthCallback();

    // Get auth status
    refreshAuth().finally(() => setIsLoading(false));

    // Listen for logout events (from axios interceptor)
    const handleLogoutEvent = () => {
      setUser(null);
    };
    window.addEventListener('auth:logout', handleLogoutEvent);

    return () => {
      window.removeEventListener('auth:logout', handleLogoutEvent);
    };
  }, [refreshAuth]);

  const login = useCallback(() => {
    loginWithGoogle();
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearStoredToken();
      setUser(null);
    }
  }, []);

  const value: AuthContextValue = {
    user,
    isAuthenticated: !!user,
    isLoading,
    oauthConfigured,
    login,
    logout,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// ============================================================================
// Hook
// ============================================================================

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export { AuthContext };
