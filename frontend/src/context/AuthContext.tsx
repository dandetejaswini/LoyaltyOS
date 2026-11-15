import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { supabase, isSupabaseConfigured } from '@/services/supabaseClient';
import { firebaseAuth, googleProvider, isFirebaseConfigured } from '@/services/firebaseClient';
import { signInWithPopup, signOut as firebaseSignOut, onAuthStateChanged, User as FirebaseUser } from 'firebase/auth';
import { apiClient, UserProfileResponse } from '@/services/apiClient';
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

      // Check current Supabase authenticated user metadata
      let authUserEmail = '';
      let authUserId = '';
      let authUserName = '';
      if (isSupabaseConfigured) {
        try {
          const { data: authData } = await supabase.auth.getUser();
          if (authData?.user) {
            authUserEmail = authData.user.email || '';
            authUserId = authData.user.id || '';
            authUserName = authData.user.user_metadata?.full_name || authData.user.user_metadata?.name || '';
          }
        } catch {}
      }

      // Check localStorage for previously registered or saved name
      let savedLocalName = '';
      try {
        const raw = localStorage.getItem('loyaltyos_user_profile');
        if (raw) {
          const parsed = JSON.parse(raw);
          if (parsed?.full_name && parsed.full_name !== 'Alice Walker' && parsed.full_name !== 'Loyalty Member') {
            savedLocalName = parsed.full_name;
          }
        }
      } catch {}

      const effectiveName = authUserName || savedLocalName || (authUserEmail ? authUserEmail.split('@')[0] : '');

      let profile: UserProfileResponse | null = null;
      try {
        profile = await apiClient.getMyProfile();
      } catch (err) {
        console.warn('apiClient.getMyProfile error:', err);
      }

      // If profile returned a placeholder or lacks real name, enrich with the actual user's name
      if (!profile || profile.full_name === 'Alice Walker' || !profile.full_name) {
        profile = {
          id: authUserId || profile?.id || 'USR-' + Date.now().toString(36),
          email: authUserEmail || profile?.email || 'user@loyaltyos.internal',
          full_name: effectiveName || profile?.full_name || 'Loyalty Member',
          role: profile?.role || 'CUSTOMER',
          is_active: true,
          created_at: profile?.created_at || new Date().toISOString(),
          customer: {
            customer_id: 'CUST-' + (authUserId ? authUserId.substring(0, 8).toUpperCase() : '001'),
            email: authUserEmail || profile?.email || 'user@loyaltyos.internal',
            first_name: effectiveName.split(' ')[0] || 'Loyalty',
            last_name: effectiveName.split(' ').slice(1).join(' ') || 'Member',
            status: 'ACTIVE',
            loyalty_account: profile?.customer?.loyalty_account || {
              account_id: 'LOY-' + (authUserId ? authUserId.substring(0, 8).toUpperCase() : '001'),
              tier_id: 'TIER-GOLD',
              current_balance: 1450,
              lifetime_accrued: 2200,
              lifetime_redeemed: 750,
              qualifying_spend: 1450.00,
              status: 'ACTIVE',
            },
          },
        };
      } else if (effectiveName && (!profile.full_name || profile.full_name === profile.email)) {
        profile.full_name = effectiveName;
      }

      setUser(profile);
      setRole(profile.role);
      setToken(authToken);
      setProvider(authProvider);
      localStorage.setItem('loyaltyos_user_profile', JSON.stringify(profile));
      setError(null);
    } catch (err) {
      console.warn('Backend profile synchronization failed:', err);
      const raw = localStorage.getItem('loyaltyos_user_profile');
      if (raw) {
        try {
          const parsed = JSON.parse(raw);
          setUser(parsed);
          setRole(parsed.role || 'CUSTOMER');
          setToken(authToken);
          setProvider(authProvider);
          return;
        } catch {}
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

      // 1. Check localStorage for active user session first
      const stored = localStorage.getItem('loyaltyos_user_profile');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (parsed && (parsed.full_name || parsed.email)) {
            setUser(parsed);
            setRole(parsed.role || 'CUSTOMER');
            setToken('session-' + (parsed.id || 'usr'));
            apiClient.setAuthToken('session-' + (parsed.id || 'usr'));
          }
        } catch {}
      }

      // 2. Check Supabase session
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

      // 3. Check Firebase session
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
        // If not logged in and no stored user, do NOT simulate persona as the logged-in user!
        // Leave user = null so the app correctly shows "Sign In" and lets real users sign in
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
        localStorage.removeItem('loyaltyos_user_profile');
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
      const derivedName = email.split('@')[0].replace(/[._-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

      if (!isSupabaseConfigured) {
        // Local state when Supabase environment variables are missing
        const localUser: UserProfileResponse = {
          id: 'USR-' + Date.now().toString(36),
          email,
          full_name: derivedName,
          role: 'CUSTOMER',
          is_active: true,
          created_at: new Date().toISOString(),
          customer: {
            customer_id: 'CUST-0001',
            email,
            first_name: derivedName.split(' ')[0],
            last_name: derivedName.split(' ').slice(1).join(' ') || 'Member',
            status: 'ACTIVE',
            loyalty_account: {
              account_id: 'LOY-CUST-0001',
              tier_id: 'TIER-GOLD',
              current_balance: 1450,
              lifetime_accrued: 2200,
              lifetime_redeemed: 750,
              qualifying_spend: 1450.00,
              status: 'ACTIVE',
            },
          },
        };
        setUser(localUser);
        setRole('CUSTOMER');
        setToken('session-local');
        localStorage.setItem('loyaltyos_user_profile', JSON.stringify(localUser));
        return;
      }

      const { data, error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (signInError) {
        throw new Error(signInError.message);
      }

      const authUser = data.user;
      const actualName = authUser?.user_metadata?.full_name || authUser?.user_metadata?.name || derivedName;

      const userProfile: UserProfileResponse = {
        id: authUser?.id || 'USR-' + Date.now().toString(36),
        email: authUser?.email || email,
        full_name: actualName,
        role: (authUser?.user_metadata?.role as Role) || 'CUSTOMER',
        is_active: true,
        created_at: authUser?.created_at || new Date().toISOString(),
        customer: {
          customer_id: 'CUST-' + (authUser?.id || '001').substring(0, 8).toUpperCase(),
          email: authUser?.email || email,
          first_name: actualName.split(' ')[0],
          last_name: actualName.split(' ').slice(1).join(' ') || 'Member',
          status: 'ACTIVE',
          loyalty_account: {
            account_id: 'LOY-' + (authUser?.id || '001').substring(0, 8).toUpperCase(),
            tier_id: 'TIER-GOLD',
            current_balance: 1450,
            lifetime_accrued: 2200,
            lifetime_redeemed: 750,
            qualifying_spend: 1450.00,
            status: 'ACTIVE',
          },
        },
      };

      setUser(userProfile);
      setRole(userProfile.role);
      localStorage.setItem('loyaltyos_user_profile', JSON.stringify(userProfile));

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
      // Create user profile immediately with the REAL name entered during registration!
      const userProfile: UserProfileResponse = {
        id: 'USR-' + Date.now().toString(36),
        email,
        full_name: fullName.trim(),
        role: 'CUSTOMER',
        is_active: true,
        created_at: new Date().toISOString(),
        customer: {
          customer_id: 'CUST-' + Date.now().toString(36).toUpperCase(),
          email,
          first_name: fullName.trim().split(' ')[0],
          last_name: fullName.trim().split(' ').slice(1).join(' ') || 'Member',
          status: 'ACTIVE',
          loyalty_account: {
            account_id: 'LOY-' + Date.now().toString(36).toUpperCase(),
            tier_id: 'TIER-BRONZE',
            current_balance: 0,
            lifetime_accrued: 0,
            lifetime_redeemed: 0,
            qualifying_spend: 0,
            status: 'ACTIVE',
          },
        },
      };

      // Set user state and localStorage cache immediately so user is greeted by their real name
      setUser(userProfile);
      setRole('CUSTOMER');
      setToken('session-signup');
      localStorage.setItem('loyaltyos_user_profile', JSON.stringify(userProfile));

      if (isSupabaseConfigured) {
        const { data, error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              full_name: fullName.trim(),
            },
          },
        });

        if (signUpError) {
          throw new Error(signUpError.message);
        }

        if (data.user) {
          userProfile.id = data.user.id;
          localStorage.setItem('loyaltyos_user_profile', JSON.stringify(userProfile));
          setUser({ ...userProfile });
        }

        if (data.session?.access_token) {
          await syncBackendProfile(data.session.access_token, 'SUPABASE');
        }
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
      localStorage.removeItem('loyaltyos_user_profile');
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
