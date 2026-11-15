import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { Lock, Mail, User, AlertCircle, Loader2, CheckCircle2 } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

export const SignUpPage: React.FC = () => {
  const navigate = useNavigate();
  const { signUpWithEmail, signInWithGoogle, isLoading, error, clearError } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [successNotice, setSuccessNotice] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessNotice(null);
    clearError();

    if (!fullName.trim() || !email.trim() || !password) {
      setLocalError('Please complete all required fields.');
      return;
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters.');
      return;
    }

    if (password !== confirmPassword) {
      setLocalError('Passwords do not match.');
      return;
    }

    try {
      setIsSubmitting(true);
      await signUpWithEmail(email.trim(), password, fullName.trim());
      setSuccessNotice('Registration successful! Redirecting to your LoyaltyOS dashboard...');
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Registration failed.';
      setLocalError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleSignUp = async () => {
    setLocalError(null);
    clearError();

    try {
      setIsSubmitting(true);
      await signInWithGoogle();
      navigate('/dashboard');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Google onboarding failed.';
      setLocalError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeError = localError || error;

  return (
    <PageContainer className="max-w-md py-12">
      <div className="card-surface p-8 shadow-sm">
        <div className="text-center mb-6">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-lavender-500 to-navy-900 border border-lavender-400/30 flex items-center justify-center mx-auto mb-3 font-bold text-sm text-white shadow-sm">
            L<span className="text-lavender-300">O</span>
          </div>
          <h1 className="text-xl font-bold text-navy-950">Join LoyaltyOS</h1>
          <p className="text-xs text-platinum-500 mt-1">Automatic loyalty ledger account provisioning upon signup</p>
        </div>

        {activeError && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-800 flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1 leading-relaxed">
              <span className="font-semibold block">Registration Error:</span>
              {activeError}
            </div>
          </div>
        )}

        {successNotice && (
          <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-800 flex items-start space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1 leading-relaxed font-medium">
              {successNotice}
            </div>
          </div>
        )}

        <button
          type="button"
          onClick={handleGoogleSignUp}
          disabled={isSubmitting || isLoading}
          className="w-full mb-4 py-2 px-4 border border-platinum-300 rounded-lg text-xs font-semibold text-platinum-800 bg-white hover:bg-platinum-50 transition flex items-center justify-center space-x-2 shadow-sm disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24">
            <path
              fill="#4285F4"
              d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
            />
            <path
              fill="#34A853"
              d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
            />
            <path
              fill="#FBBC05"
              d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
            />
            <path
              fill="#EA4335"
              d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
            />
          </svg>
          <span>Sign up with Google</span>
        </button>

        <div className="relative mb-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-platinum-200"></div>
          </div>
          <div className="relative flex justify-center text-xs">
            <span className="px-2 bg-white text-platinum-400 font-medium">Or register with email</span>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-platinum-700 mb-1">Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 text-platinum-400 absolute left-3 top-2.5" />
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Jane Doe"
                disabled={isSubmitting || isLoading}
                className="input-field pl-9"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-platinum-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-platinum-400 absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="jane@example.com"
                disabled={isSubmitting || isLoading}
                className="input-field pl-9"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-platinum-700 mb-1">Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-platinum-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="At least 6 characters"
                disabled={isSubmitting || isLoading}
                className="input-field pl-9"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-platinum-700 mb-1">Confirm Password</label>
            <div className="relative">
              <Lock className="w-4 h-4 text-platinum-400 absolute left-3 top-2.5" />
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                disabled={isSubmitting || isLoading}
                className="input-field pl-9"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || isLoading}
            className="w-full btn-primary flex items-center justify-center space-x-1"
          >
            {isSubmitting || isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-1" />
                <span>Creating Account...</span>
              </>
            ) : (
              <span>Create Account</span>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-platinum-200 text-center">
          <p className="text-xs text-platinum-600">
            Already have an account?{' '}
            <Link to="/sign-in" className="text-lavender-600 hover:text-lavender-700 font-medium">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </PageContainer>
  );
};
