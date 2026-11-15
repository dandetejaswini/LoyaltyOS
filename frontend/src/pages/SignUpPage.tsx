import React from 'react';
import { Link } from 'react-router-dom';
import { PageContainer } from '@/components/layout/PageContainer';
import { Mail, User } from 'lucide-react';

export const SignUpPage: React.FC = () => {
  return (
    <PageContainer className="max-w-md">
      <div className="bg-white border border-platinum-200 rounded-xl p-8 shadow-sm">
        <div className="text-center mb-6">
          <div className="w-10 h-10 rounded-lg bg-navy-950 text-white flex items-center justify-center mx-auto mb-3 font-bold text-sm border border-navy-800 shadow-sm">
            L<span className="text-lavender-400">O</span>
          </div>
          <h1 className="text-xl font-bold text-navy-950">Join LoyaltyOS</h1>
          <p className="text-xs text-platinum-500 mt-1">Automatic loyalty ledger account provisioning upon signup</p>
        </div>

        <div className="mb-4 p-3 bg-lavender-50 border border-lavender-200 rounded-lg text-xs text-navy-950 leading-relaxed">
          <span className="font-semibold text-lavender-900 block mb-0.5">Phase 1 Foundation:</span>
          Live onboarding pipelines will be connected to Supabase Auth and automatic LoyaltyAccount provisioning in Phase 2.
        </div>

        <form onSubmit={(e) => e.preventDefault()} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-platinum-700 mb-1">Full Name</label>
            <div className="relative">
              <User className="w-4 h-4 text-platinum-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Jane Doe"
                disabled
                className="w-full pl-9 pr-3 py-2 bg-platinum-50 border border-platinum-300 rounded-lg text-xs text-platinum-700 cursor-not-allowed"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-platinum-700 mb-1">Email Address</label>
            <div className="relative">
              <Mail className="w-4 h-4 text-platinum-400 absolute left-3 top-2.5" />
              <input
                type="email"
                placeholder="jane@example.com"
                disabled
                className="w-full pl-9 pr-3 py-2 bg-platinum-50 border border-platinum-300 rounded-lg text-xs text-platinum-700 cursor-not-allowed"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled
            className="w-full py-2 bg-platinum-200 text-platinum-500 rounded-lg text-xs font-medium cursor-not-allowed transition"
          >
            Register (Phase 2 Integration)
          </button>
        </form>

        <div className="mt-6 pt-4 border-t border-platinum-200 text-center">
          <p className="text-xs text-platinum-600">
            Already registered?{' '}
            <Link to="/sign-in" className="text-lavender-600 hover:text-lavender-700 font-medium">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </PageContainer>
  );
};
