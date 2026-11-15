import { UserProfileResponse } from '@/services/apiClient';

export type Role = 'CUSTOMER' | 'OPERATOR' | 'ANALYST' | 'OPERATIONS_MANAGER';

export type AuthProviderType = 'SUPABASE' | 'FIREBASE';

export interface AuthContextValue {
  user: UserProfileResponse | null;
  token: string | null;
  role: Role | null;
  provider: AuthProviderType | null;
  isLoading: boolean;
  error: string | null;
  signInWithEmail: (email: string, password: string) => Promise<void>;
  signUpWithEmail: (email: string, password: string, fullName: string) => Promise<void>;
  signInWithGoogle: () => Promise<void>;
  signOut: () => Promise<void>;
  clearError: () => void;
}
