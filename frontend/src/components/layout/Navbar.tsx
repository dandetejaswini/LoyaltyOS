import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, ArrowRight, LogOut, User as UserIcon } from 'lucide-react';
import { useAuth } from '@/hooks/useAuth';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const { user, signOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navLinks = [
    { label: 'Home', path: '/' },
    { label: 'About', path: '/about' },
    { label: 'Features', path: '/features' },
    { label: 'Contact', path: '/contact' },
    { label: 'Workspace', path: '/workspace', isAction: true },
  ];

  const isActive = (path: string) => {
    if (path === '/workspace') {
      return location.pathname === '/workspace' || location.pathname === '/dashboard';
    }
    return location.pathname === path;
  };

  return (
    <header className="bg-navy-950/95 backdrop-blur-md border-b border-navy-800 text-white sticky top-0 z-50 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Identity */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-lavender-500 to-navy-900 border border-lavender-400/30 flex items-center justify-center shadow-md relative overflow-hidden transition transform group-hover:scale-105">
              <span className="font-extrabold text-sm tracking-tight text-white">
                L<span className="text-lavender-300">O</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-white group-hover:text-lavender-100 transition">
                Loyalty<span className="text-lavender-400">OS</span>
              </span>
              <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-semibold tracking-wider bg-navy-900/90 text-lavender-300 rounded-full border border-lavender-500/20 shadow-sm">
                Enterprise
              </span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1.5">
            {navLinks.map((link) => {
              const active = isActive(link.path);
              if (link.isAction) {
                return (
                  <Link
                    key={link.path}
                    to={link.path}
                    className={`ml-2 px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-sm ${
                      active
                        ? 'bg-lavender-600 text-white border border-lavender-400'
                        : 'bg-lavender-600/90 hover:bg-lavender-600 text-white border border-lavender-500/40 hover:shadow'
                    }`}
                  >
                    <span>{link.label}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-lavender-200" />
                  </Link>
                );
              }
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-3.5 py-2 rounded-lg text-xs font-medium transition ${
                    active
                      ? 'bg-navy-900 text-lavender-300 font-semibold border border-navy-700'
                      : 'text-platinum-300 hover:text-white hover:bg-navy-900/60'
                  }`}
                >
                  {link.label}
                </Link>
              );
            })}
          </nav>

          {/* Right User State */}
          <div className="hidden sm:flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-2.5">
                <Link
                  to="/settings"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-navy-900/80 hover:bg-navy-800 text-platinum-300 border border-navy-700 text-xs transition"
                >
                  <UserIcon className="w-3.5 h-3.5 text-lavender-400" />
                  <span className="truncate max-w-[130px] font-medium">{user.full_name || user.email}</span>
                </Link>
                <button
                  onClick={() => signOut()}
                  title="Sign Out"
                  className="p-1.5 text-platinum-400 hover:text-white hover:bg-navy-800 rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                to="/sign-in"
                className="px-3.5 py-1.5 text-xs font-medium text-platinum-200 hover:text-white rounded-lg hover:bg-navy-900 transition border border-transparent hover:border-navy-700"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-platinum-400 hover:text-white hover:bg-navy-800 rounded-lg transition"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-navy-900 border-b border-navy-800 px-4 pt-3 pb-5 space-y-2">
          {navLinks.map((link) => {
            const active = isActive(link.path);
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2 rounded-lg text-xs font-medium ${
                  active
                    ? 'bg-lavender-600 text-white font-semibold'
                    : 'text-platinum-300 hover:bg-navy-800 hover:text-white'
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <div className="pt-3 border-t border-navy-800 flex items-center justify-between">
            {user ? (
              <>
                <span className="text-xs text-platinum-400 truncate">{user.email}</span>
                <button
                  onClick={() => {
                    signOut();
                    setMobileMenuOpen(false);
                  }}
                  className="text-xs text-rose-400 font-medium"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <Link
                to="/sign-in"
                onClick={() => setMobileMenuOpen(false)}
                className="text-xs text-lavender-300 font-medium"
              >
                Sign In to Account
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
