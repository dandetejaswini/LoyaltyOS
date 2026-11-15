import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { Mail, ArrowLeft } from 'lucide-react';

export const ForgotPasswordPage: React.FC = () => {
  return (
    <PageContainer className="max-w-md">
      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
        <div className="text-center mb-6">
          <h1 className="text-xl font-bold text-slate-900">Reset Password</h1>
          <p className="text-xs text-slate-500 mt-1">
            Enter your verified email to receive a password reset link.
          </p>
        </div>

        <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="email"
                placeholder="user@example.com"
                disabled
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded text-xs text-slate-700 cursor-not-allowed"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled
            className="w-full py-2 bg-slate-300 text-slate-600 rounded text-xs font-medium cursor-not-allowed transition"
          >
            Send Reset Link (Phase 2 Integration)
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-200 text-center">
          <Link to="/sign-in" className="inline-flex items-center gap-1.5 text-xs text-brand-600 hover:text-brand-700 font-medium">
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Sign In
          </Link>
        </div>
      </div>
    </PageContainer>
  );
};
