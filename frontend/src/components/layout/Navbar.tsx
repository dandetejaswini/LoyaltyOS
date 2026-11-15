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
    <header className="bg-white/95 backdrop-blur-md border-b border-pastel-border text-pastel-dark sticky top-0 z-50 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Brand Identity */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-9 h-9 rounded-xl bg-pastel-lavender border border-pastel-border flex items-center justify-center shadow-xs transition transform group-hover:scale-105">
              <span className="font-extrabold text-sm tracking-tight text-pastel-dark">
                L<span className="text-pastel-sageDark">O</span>
              </span>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight text-pastel-dark group-hover:text-pastel-dark/80 transition">
                Loyalty<span className="text-pastel-lavenderDark">OS</span>
              </span>
              <span className="hidden sm:inline-block px-2.5 py-0.5 text-[10px] font-semibold tracking-wider bg-pastel-sage text-pastel-dark rounded-full border border-pastel-border shadow-xs">
                Platform
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
                    className={`ml-2 px-4 py-2 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs ${
                      active
                        ? 'bg-pastel-sage text-pastel-dark border border-pastel-border font-bold'
                        : 'bg-pastel-sage/80 hover:bg-pastel-sage text-pastel-dark border border-pastel-border'
                    }`}
                  >
                    <span>{link.label}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-pastel-dark" />
                  </Link>
                );
              }
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`px-3.5 py-2 rounded-lg text-xs font-medium transition ${
                    active
                      ? 'bg-pastel-ivory text-pastel-dark font-semibold border border-pastel-border'
                      : 'text-pastel-muted hover:text-pastel-dark hover:bg-pastel-ivory'
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
                  to="/workspace"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-pastel-ivory hover:bg-pastel-sage/50 text-pastel-dark border border-pastel-border text-xs transition"
                  title="Operational Workspace"
                >
                  <UserIcon className="w-3.5 h-3.5 text-pastel-muted" />
                  <span className="truncate max-w-[130px] font-medium">{user.full_name || user.email}</span>
                </Link>
                <button
                  onClick={() => signOut()}
                  title="Sign Out"
                  className="p-1.5 text-pastel-muted hover:text-pastel-dark hover:bg-pastel-ivory rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                to="/sign-in"
                className="px-3.5 py-1.5 text-xs font-medium text-pastel-dark hover:text-pastel-dark rounded-lg bg-white hover:bg-pastel-ivory transition border border-pastel-border shadow-xs"
              >
                Sign In
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-pastel-muted hover:text-pastel-dark hover:bg-pastel-ivory rounded-lg transition"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-pastel-border px-4 pt-3 pb-5 space-y-2">
          {navLinks.map((link) => {
            const active = isActive(link.path);
            return (
              <Link
                key={link.path}
                to={link.path}
                onClick={() => setMobileMenuOpen(false)}
                className={`block px-3 py-2 rounded-lg text-xs font-medium ${
                  active
                    ? 'bg-pastel-sage text-pastel-dark font-semibold'
                    : 'text-pastel-muted hover:bg-pastel-ivory hover:text-pastel-dark'
                }`}
              >
                {link.label}
              </Link>
            );
          })}
          <div className="pt-3 border-t border-pastel-border flex items-center justify-between">
            {user ? (
              <>
                <span className="text-xs text-pastel-muted truncate">{user.email}</span>
                <button
                  onClick={() => {
                    signOut();
                    setMobileMenuOpen(false);
                  }}
                  className="text-xs text-pastel-roseDark font-medium"
                >
                  Sign Out
                </button>
              </>
            ) : (
              <Link
                to="/sign-in"
                onClick={() => setMobileMenuOpen(false)}
                className="text-xs text-pastel-dark font-medium"
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
