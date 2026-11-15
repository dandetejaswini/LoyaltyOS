import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { Lock, Mail } from 'lucide-react';

export const SignInPage: React.FC = () => {
  return (
    <PageContainer className="max-w-md">
      <div className="bg-white border border-slate-200 rounded-xl p-8 shadow-sm">
        <div className="text-center mb-6">
          <div className="w-10 h-10 rounded-full bg-brand-50 text-brand-700 flex items-center justify-center mx-auto mb-2 font-bold text-sm">
            YF
          </div>
          <h1 className="text-xl font-bold text-slate-900">Sign in to YottaFlex</h1>
          <p className="text-xs text-slate-500 mt-1">Enterprise Loyalty & Operations Portal</p>
        </div>

        <div className="mb-4 p-3 bg-brand-50 border border-brand-200 rounded text-xs text-brand-900 leading-relaxed">
          <span className="font-semibold block mb-0.5">Phase 1 Foundation Notice:</span>
          Authentication credentials will be securely validated against Supabase Auth (Email/Password) and Firebase Auth (Google OAuth) starting in Phase 2.
        </div>

        <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="email"
                placeholder="operator@yottaflex.io"
                disabled
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded text-xs text-slate-700 cursor-not-allowed"
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="text-xs font-semibold text-slate-700">Password</label>
              <Link to="/forgot-password" className="text-xs text-brand-600 hover:text-brand-700">
                Forgot password?
              </Link>
            </div>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="password"
                placeholder="••••••••••••"
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
            Sign In (Phase 2 Integration)
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-slate-200 text-center">
          <p className="text-xs text-slate-600">
            Don't have an account?{' '}
            <Link to="/sign-up" className="text-brand-600 hover:text-brand-700 font-medium">
              Register here
            </Link>
          </p>
        </div>
      </div>
    </PageContainer>
  );
};
