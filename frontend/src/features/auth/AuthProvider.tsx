import { createContext, ReactNode, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import {
  clearStoredAccessToken,
  fetchCurrentUser,
  getStoredAccessToken,
  login as loginRequest,
  signup as signupRequest,
  storeAccessToken,
} from "../../services/api";
import type { AuthResponse, AuthUser } from "../../types/api";

type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (payload: { identifier: string; password: string }) => Promise<AuthUser>;
  signup: (payload: { username: string; email: string; password: string }) => Promise<AuthUser>;
  logout: () => void;
  refreshSession: () => Promise<AuthUser | null>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

type Props = {
  children: ReactNode;
};

export function AuthProvider({ children }: Props) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const applyAuthResponse = (response: AuthResponse) => {
    storeAccessToken(response.access_token);
    setUser(response.user);
    queryClient.clear();
    return response.user;
  };

  const logout = () => {
    clearStoredAccessToken();
    setUser(null);
    queryClient.clear();
  };

  const refreshSession = async () => {
    if (!getStoredAccessToken()) {
      setUser(null);
      return null;
    }

    const currentUser = await fetchCurrentUser();
    setUser(currentUser);
    return currentUser;
  };

  useEffect(() => {
    let isMounted = true;

    const bootstrapSession = async () => {
      if (!getStoredAccessToken()) {
        if (isMounted) {
          setIsLoading(false);
        }
        return;
      }

      try {
        const currentUser = await fetchCurrentUser();
        if (isMounted) {
          setUser(currentUser);
        }
      } catch {
        clearStoredAccessToken();
        if (isMounted) {
          setUser(null);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    const handleExpired = () => {
      if (!isMounted) {
        return;
      }
      clearStoredAccessToken();
      setUser(null);
      setIsLoading(false);
      queryClient.clear();
    };

    void bootstrapSession();
    window.addEventListener("song-master-auth-expired", handleExpired);

    return () => {
      isMounted = false;
      window.removeEventListener("song-master-auth-expired", handleExpired);
    };
  }, [queryClient]);

  const value: AuthContextValue = {
    user,
    isAuthenticated: Boolean(user),
    isLoading,
    login: async (payload) => applyAuthResponse(await loginRequest(payload)),
    signup: async (payload) => applyAuthResponse(await signupRequest(payload)),
    logout,
    refreshSession,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}