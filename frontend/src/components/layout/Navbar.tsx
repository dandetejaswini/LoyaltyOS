import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X } from 'lucide-react';
import { apiClient, HealthResponse } from '@/services/apiClient';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let mounted = true;
    apiClient
      .getHealth()
      .then((data) => {
        if (mounted) setHealth(data);
      })
      .catch(() => {
        if (mounted) setHealth(null);
      });
    return () => {
      mounted = false;
    };
  }, []);

  const navLinks = [
    { label: 'Overview', path: '/' },
    { label: 'About Ledger', path: '/about' },
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Settings', path: '/settings' },
  ];

  return (
    <header className="bg-brand-950 border-b border-brand-900 text-white sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-inner font-bold text-sm tracking-wider">
                YF
              </div>
              <div>
                <span className="font-semibold text-base tracking-tight text-white">YottaFlex</span>
                <span className="hidden sm:inline-block ml-2 px-1.5 py-0.5 text-[10px] uppercase font-mono tracking-wider bg-brand-900 text-brand-300 rounded border border-brand-800">
                  Ledger Core
                </span>
              </div>
            </Link>
          </div>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => {
              const active = location.pathname === link.path;
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-3 py-1.5 rounded text-xs font-medium transition ${
                    active
                      ? 'bg-brand-900 text-white border border-brand-800'
                      : 'text-slate-300 hover:text-white hover:bg-brand-900/50'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right Action / System Status */}
          <div className="hidden sm:flex items-center gap-4">
            {/* Live Health Status Pill */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-brand-900/80 border border-brand-800 text-[11px]">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'healthy'
                    ? 'bg-emerald-400 animate-pulse'
                    : health?.status === 'degraded'
                    ? 'bg-amber-400'
                    : 'bg-rose-500'
                }`}
              />
              <span className="text-slate-300 font-mono">
                {health ? `API v${health.version}` : 'Connecting...'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <Link
                to="/sign-in"
                className="px-3 py-1.5 text-xs font-medium text-slate-200 hover:text-white transition"
              >
                Sign In
              </Link>
              <Link
                to="/sign-up"
                className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white text-xs font-medium rounded transition shadow-sm"
              >
                Register Account
              </Link>
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-slate-300 hover:text-white p-2"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-brand-900 bg-brand-950 px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded text-sm font-medium ${
                location.pathname === link.path
                  ? 'bg-brand-900 text-white'
                  : 'text-slate-300 hover:bg-brand-900/50'
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-2 border-t border-brand-900 flex flex-col gap-2">
            <Link
              to="/sign-in"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm text-center text-slate-300 hover:text-white"
            >
              Sign In
            </Link>
            <Link
              to="/sign-up"
              onClick={() => setMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm text-center bg-brand-600 text-white rounded font-medium"
            >
              Register Account
            </Link>
          </div>
        </div>
      )}
    </header>
  );
};
