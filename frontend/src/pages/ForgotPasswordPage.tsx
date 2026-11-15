import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { Mail, ArrowLeft, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';
import { supabase, isSupabaseConfigured } from '@/services/supabaseClient';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setSuccessMessage(null);

    if (!email.trim()) {
      setErrorMessage('Please enter your account email address.');
      return;
    }

    try {
      setIsSubmitting(true);
      if (!isSupabaseConfigured) {
        setSuccessMessage('Password reset instructions will be sent if the email exists in LoyaltyOS directory.');
        return;
      }

      const { error } = await supabase.auth.resetPasswordForEmail(email.trim(), {
        redirectTo: `${window.location.origin}/sign-in`,
      });

      if (error) {
        throw new Error(error.message);
      }

      setSuccessMessage('Password reset link has been dispatched to your email address.');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to send password reset request.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageContainer className="max-w-md py-12">
      <div className="bg-white border border-pastel-border rounded-2xl p-8 shadow-xs">
        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-pastel-lavender text-pastel-dark border border-pastel-border flex items-center justify-center mx-auto mb-3 font-bold text-base shadow-xs">
            L<span className="text-pastel-lavenderDark">O</span>
          </div>
          <h1 className="text-xl font-bold text-pastel-dark">Reset Password</h1>
          <p className="text-xs text-pastel-muted mt-1 leading-relaxed">
            Enter your verified email to receive a secure password recovery link.
          </p>
        </div>

        {errorMessage && (
          <div className="mb-4 p-3.5 bg-pastel-rose/50 border border-pastel-border rounded-xl text-xs text-pastel-dark flex items-start space-x-2">
            <AlertCircle className="w-4 h-4 text-pastel-roseDark flex-shrink-0 mt-0.5" />
            <div className="flex-1 leading-relaxed">
              <span className="font-semibold block text-pastel-roseDark">Request Error:</span>
              {errorMessage}
            </div>
          </div>
        )}

        {successMessage && (
          <div className="mb-4 p-3.5 bg-pastel-sage/50 border border-pastel-border rounded-xl text-xs text-pastel-dark flex items-start space-x-2">
            <CheckCircle2 className="w-4 h-4 text-pastel-sageDark flex-shrink-0 mt-0.5" />
            <div className="flex-1 leading-relaxed font-medium">
              {successMessage}
            </div>
          </div>
        )}

        <form onSubmit={handleResetPassword} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-pastel-dark mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-pastel-muted absolute left-3 top-2.5" />
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                disabled={isSubmitting}
                className="input-field pl-9"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full btn-primary flex items-center justify-center space-x-1.5 shadow-xs"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin mr-1" />
                <span>Sending Reset Link...</span>
              </>
            ) : (
              <span>Send Recovery Link</span>
            )}
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-pastel-border text-center">
          <Link to="/sign-in" className="inline-flex items-center gap-1.5 text-xs text-pastel-dark hover:text-pastel-muted font-bold transition">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Sign In
          </Link>
        </div>
      </div>
    </PageContainer>
  );
};
