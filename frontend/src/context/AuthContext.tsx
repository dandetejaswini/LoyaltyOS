import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { supabase, isSupabaseConfigured } from '@/services/supabaseClient';
import { firebaseAuth, googleProvider, isFirebaseConfigured } from '@/services/firebaseClient';
import { signInWithPopup, signOut as firebaseSignOut, onAuthStateChanged, User as FirebaseUser } from 'firebase/auth';
import { apiClient, UserProfileResponse, ApiError } from '@/services/apiClient';
import { AuthContextValue, AuthProviderType, Role } from '@/types/auth';

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfileResponse | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [role, setRole] = useState<Role | null>(null);
  const [provider, setProvider] = useState<AuthProviderType | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const simulatePersona = useCallback((targetRole: Role, variant = 1) => {
    let mockUser: UserProfileResponse;
    if (targetRole === 'OPERATIONS_MANAGER') {
      if (variant === 2) {
        mockUser = {
          id: 'USR-MGR-002',
          email: 'admin@loyaltyos.internal',
          full_name: 'David Kim (VP Loyalty Risk & Approvals)',
          role: 'OPERATIONS_MANAGER',
          is_active: true,
          created_at: new Date().toISOString(),
        };
      } else {
        mockUser = {
          id: 'USR-MGR-001',
          email: 'manager@loyaltyos.internal',
          full_name: 'Eleanor Vance (Operations Director)',
          role: 'OPERATIONS_MANAGER',
          is_active: true,
          created_at: new Date().toISOString(),
        };
      }
    } else if (targetRole === 'OPERATOR') {
      mockUser = {
        id: 'USR-OP-001',
        email: 'operator@loyaltyos.internal',
        full_name: 'Marcus Brody (Fulfillment Lead)',
        role: 'OPERATOR',
        is_active: true,
        created_at: new Date().toISOString(),
      };
    } else if (targetRole === 'ANALYST') {
      mockUser = {
        id: 'USR-ANA-001',
        email: 'analyst@loyaltyos.internal',
        full_name: 'Sarah Chen (Risk & Fraud Analyst)',
        role: 'ANALYST',
        is_active: true,
        created_at: new Date().toISOString(),
      };
    } else {
      mockUser = {
        id: 'USR-CUST-001',
        email: 'alice@example.com',
        full_name: 'Alice Sterling (VIP Member)',
        role: 'CUSTOMER',
        is_active: true,
        customer: {
          customer_id: 'CUST-000001',
          email: 'alice@example.com',
          first_name: 'Alice',
          last_name: 'Sterling',
          status: 'ACTIVE',
          loyalty_account: {
            account_id: 'LOY-CUST-000001',
            tier_id: 'TIER-PLATINUM',
            current_balance: 2095,
            lifetime_accrued: 4002,
            lifetime_redeemed: 1450,
            qualifying_spend: '2634.27',
            status: 'ACTIVE',
          },
        },
        created_at: new Date().toISOString(),
      };
    }

    setUser(mockUser);
    setRole(mockUser.role);
    setToken(`demo-session-${mockUser.id}`);
    apiClient.setAuthToken(`demo-session-${mockUser.id}`);
    setError(null);
  }, []);

  const syncBackendProfile = useCallback(async (authToken: string, authProvider: AuthProviderType) => {
    try {
      apiClient.setAuthToken(authToken);
      const profile = await apiClient.getMyProfile();
      setUser(profile);
      setRole(profile.role);
      setToken(authToken);
      setProvider(authProvider);
      setError(null);
    } catch (err) {
      console.warn('Backend profile synchronization failed:', err);
      if (err instanceof ApiError) {
        setError(err.problem.detail || err.problem.title);
      } else {
        setError('Failed to synchronize authentication profile with LoyaltyOS backend.');
      }
      setUser(null);
      setRole(null);
      setToken(null);
      setProvider(null);
      apiClient.setAuthToken(null);
    }
  }, []);

  // Initialize and listen to auth states
  useEffect(() => {
    let isMounted = true;

    async function initAuth() {
      setIsLoading(true);

      // Check Supabase session first
      if (isSupabaseConfigured) {
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (session?.access_token && isMounted) {
            await syncBackendProfile(session.access_token, 'SUPABASE');
            setIsLoading(false);
            return;
          }
        } catch (e) {
          console.warn('Error reading initial Supabase session:', e);
        }
      }

      // Check Firebase session
      if (firebaseAuth) {
        onAuthStateChanged(firebaseAuth, async (fbUser: FirebaseUser | null) => {
          if (!isMounted) return;
          if (fbUser) {
            try {
              const fbToken = await fbUser.getIdToken();
              await syncBackendProfile(fbToken, 'FIREBASE');
            } catch (e) {
              console.warn('Failed to retrieve Firebase ID token:', e);
            }
          }
          setIsLoading(false);
        });
      } else {
        // Default to Operations Manager persona for demonstration
        if (isMounted) {
          simulatePersona('OPERATIONS_MANAGER', 1);
        }
        setIsLoading(false);
      }
    }

    initAuth();

    // Listen to Supabase auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, session) => {
      if (!isMounted) return;
      if (event === 'SIGNED_IN' && session?.access_token) {
        await syncBackendProfile(session.access_token, 'SUPABASE');
      } else if (event === 'SIGNED_OUT') {
        setUser(null);
        setRole(null);
        setToken(null);
        setProvider(null);
        apiClient.setAuthToken(null);
      }
    });

    return () => {
      isMounted = false;
      subscription.unsubscribe();
    };
  }, [syncBackendProfile]);

  const signInWithEmail = async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    try {
      if (!isSupabaseConfigured) {
        throw new Error('Supabase Auth is not configured. Please supply VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in .env.');
      }
      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (signInError) {
        throw new Error(signInError.message);
      }

      if (data.session?.access_token) {
        await syncBackendProfile(data.session.access_token, 'SUPABASE');
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Sign in failed.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signUpWithEmail = async (email: string, password: string, fullName: string) => {
    setIsLoading(true);
    setError(null);
    try {
      if (!isSupabaseConfigured) {
        throw new Error('Supabase Auth is not configured. Please supply VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in .env.');
      }
      const { data, error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
          },
        },
      });

      if (signUpError) {
        throw new Error(signUpError.message);
      }

      if (data.session?.access_token) {
        await syncBackendProfile(data.session.access_token, 'SUPABASE');
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Registration failed.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signInWithGoogle = async () => {
    setIsLoading(true);
    setError(null);
    try {
      if (!isFirebaseConfigured || !firebaseAuth || !googleProvider) {
        throw new Error('Firebase Google Auth is not configured. Please provide VITE_FIREBASE_API_KEY and VITE_FIREBASE_PROJECT_ID in frontend/.env.');
      }
      const result = await signInWithPopup(firebaseAuth, googleProvider);
      const idToken = await result.user.getIdToken();
      await syncBackendProfile(idToken, 'FIREBASE');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Google authentication failed.';
      setError(msg);
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const signOut = async () => {
    setIsLoading(true);
    try {
      if (provider === 'SUPABASE' || isSupabaseConfigured) {
        await supabase.auth.signOut().catch(() => {});
      }
      if (provider === 'FIREBASE' || firebaseAuth) {
        if (firebaseAuth) {
          await firebaseSignOut(firebaseAuth).catch(() => {});
        }
      }
    } finally {
      setUser(null);
      setRole(null);
      setToken(null);
      setProvider(null);
      apiClient.setAuthToken(null);
      setIsLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role,
        provider,
        isLoading,
        error,
        signInWithEmail,
        signUpWithEmail,
        signInWithGoogle,
        signOut,
        clearError,
        simulatePersona,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
