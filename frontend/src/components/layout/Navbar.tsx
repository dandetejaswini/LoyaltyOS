import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, LogOut, User as UserIcon } from 'lucide-react';
import { apiClient, HealthResponse } from '@/services/apiClient';
import { useAuth } from '@/hooks/useAuth';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { user, role, signOut } = useAuth();
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
    { label: 'Architecture', path: '/about' },
    { label: 'Dashboard', path: '/dashboard' },
    { label: 'Settings', path: '/settings' },
  ];

  return (
    <header className="bg-navy-950 border-b border-navy-800 text-white sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Identity */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-navy-900 border border-navy-700 flex items-center justify-center shadow-inner relative overflow-hidden group">
                <div className="absolute inset-0 bg-gradient-to-br from-lavender-500/20 to-transparent"></div>
                <span className="font-extrabold text-sm tracking-tight text-white">
                  L<span className="text-lavender-400">O</span>
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-base tracking-tight text-white">
                  Loyalty<span className="text-lavender-400">OS</span>
                </span>
                <span className="hidden sm:inline-block px-1.5 py-0.5 text-[10px] uppercase font-mono tracking-wider bg-navy-900 text-lavender-300 rounded border border-navy-700">
                  YottaFlex
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
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                    active
                      ? 'bg-navy-800 text-lavender-200 border border-navy-700 shadow-sm'
                      : 'text-platinum-300 hover:text-white hover:bg-navy-900/60'
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
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-navy-900/90 border border-navy-700 text-[11px]">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'healthy'
                    ? 'bg-emerald-400 animate-pulse'
                    : health?.status === 'degraded'
                    ? 'bg-amber-400'
                    : 'bg-rose-500'
                }`}
              />
              <span className="text-platinum-300 font-mono">
                {health ? `Core v${health.version}` : 'Connecting...'}
              </span>
            </div>

            <div className="flex items-center gap-2">
              {user ? (
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-2 bg-navy-900 border border-navy-700 py-1 px-2.5 rounded-lg">
                    <div className="w-6 h-6 rounded-full bg-lavender-500/20 text-lavender-300 border border-lavender-400/30 flex items-center justify-center text-xs font-bold">
                      {user.full_name ? user.full_name.charAt(0).toUpperCase() : user.email.charAt(0).toUpperCase()}
                    </div>
                    <div className="text-left hidden lg:block">
                      <div className="text-xs font-semibold text-white leading-tight truncate max-w-[120px]">
                        {user.full_name || user.email.split('@')[0]}
                      </div>
                      <span className="text-[10px] text-lavender-300 font-mono">
                        {role}
                      </span>
                    </div>
                  </div>
                  <button
                    onClick={() => signOut()}
                    className="p-1.5 text-platinum-400 hover:text-white hover:bg-navy-900 rounded-md transition"
                    title="Sign Out"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <>
                  <Link
                    to="/sign-in"
                    className="px-3 py-1.5 text-xs font-medium text-platinum-300 hover:text-white transition"
                  >
                    Sign In
                  </Link>
                  <Link
                    to="/sign-up"
                    className="px-3.5 py-1.5 bg-lavender-600 hover:bg-lavender-500 text-white text-xs font-medium rounded-md transition shadow-sm"
                  >
                    Register
                  </Link>
                </>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="text-platinum-300 hover:text-white p-2"
              aria-label="Toggle Navigation Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-navy-800 bg-navy-950 px-4 pt-2 pb-4 space-y-1">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              className={`block px-3 py-2 rounded-md text-sm font-medium ${
                location.pathname === link.path
                  ? 'bg-navy-800 text-lavender-200'
                  : 'text-platinum-300 hover:bg-navy-900/60'
              }`}
            >
              {link.label}
            </Link>
          ))}
          <div className="pt-2 border-t border-navy-800 flex flex-col gap-2">
            {user ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2 px-3 py-1.5 text-xs text-platinum-300">
                  <UserIcon className="w-4 h-4 text-lavender-400" />
                  <span>{user.email}</span>
                  <span className="ml-auto text-[10px] bg-navy-900 px-1.5 py-0.5 rounded border border-navy-700 text-lavender-300">
                    {role}
                  </span>
                </div>
                <button
                  onClick={() => {
                    signOut();
                    setMobileMenuOpen(false);
                  }}
                  className="w-full text-left px-3 py-2 text-sm text-rose-400 hover:text-rose-300 hover:bg-navy-900/60 rounded-md transition flex items-center gap-2"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <>
                <Link
                  to="/sign-in"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 text-sm text-center text-platinum-300 hover:text-white"
                >
                  Sign In
                </Link>
                <Link
                  to="/sign-up"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block px-3 py-2 text-sm text-center bg-lavender-600 text-white rounded-md font-medium"
                >
                  Register
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
