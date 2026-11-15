import React, { useState } from 'react';
import { PageContainer } from '@/components/layout/PageContainer';
import {
  Mail,
  MapPin,
  Clock,
  ShieldCheck,
  Send,
  CheckCircle2,
  Building,
  HelpCircle,
  FileText,
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const ContactPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [company, setCompany] = useState('');
  const [inquiryType, setInquiryType] = useState('ENTERPRISE_DEMO');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !email || !message) return;
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      setSubmitted(true);
    }, 700);
  };

  const contactChannels = [
    {
      icon: <Building className="w-5 h-5 text-lavender-600" />,
      title: 'Enterprise & Solutions Architecture',
      desc: 'Discuss multi-tenant loyalty ledger deployments, custom ERP connectors, and high-throughput volume pricing.',
      email: 'solutions@loyaltyos.internal',
      sla: '< 2 Hours Response'
    },
    {
      icon: <ShieldCheck className="w-5 h-5 text-emerald-600" />,
      title: 'Security, Audit & Compliance',
      desc: 'Inquire about financial audit reports, PostgreSQL trigger immutability verification, and SOC2 compliance artifacts.',
      email: 'security@loyaltyos.internal',
      sla: 'Same-day SLA'
    },
    {
      icon: <HelpCircle className="w-5 h-5 text-navy-600" />,
      title: 'Developer Support & Integration',
      desc: 'Technical assistance with FastAPI endpoints, Supabase Row-Level Security, and webhook event streaming.',
      email: 'dev-support@loyaltyos.internal',
      sla: '24/7 Availability'
    }
  ];

  return (
    <PageContainer
      title="Contact LoyaltyOS"
      subtitle="Connect with our enterprise engineering team, request an architectural briefing, or report a platform inquiry."
    >
      {/* Hero Banner with Image */}
      <div className="relative overflow-hidden rounded-2xl bg-navy-950 text-white p-8 sm:p-12 mb-10 border border-navy-800 shadow-lg">
        <div className="absolute inset-0 opacity-15 mix-blend-overlay pointer-events-none">
          <img
            src="https://images.unsplash.com/photo-1522071820081-009f0129c71c?auto=format&fit=crop&w=1600&q=80"
            alt="LoyaltyOS Engineering Team"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-lavender-900/60 border border-lavender-700/60 text-lavender-300 text-xs font-semibold mb-4">
            <Clock className="w-3.5 h-3.5 text-lavender-400" />
            Enterprise Support Desk • Direct Access
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-3">
            We are here to assist with your ledger architecture.
          </h1>
          <p className="text-sm sm:text-base text-platinum-300 leading-relaxed">
            Whether you are evaluating double-entry ledger reconciliation, deploying LLIRE fraud intelligence, or auditing retail point liability, our team responds directly.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 mb-12">
        {/* Contact Form (7 cols) */}
        <div className="lg:col-span-7 bg-white border border-platinum-200 rounded-xl p-6 sm:p-8 shadow-sm">
          {submitted ? (
            <div className="text-center py-10 space-y-4">
              <div className="w-14 h-14 bg-emerald-50 border border-emerald-200 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-bold text-navy-950">Inquiry Received Successfully</h3>
              <p className="text-sm text-platinum-600 max-w-md mx-auto">
                Thank you for contacting LoyaltyOS, <strong className="text-navy-950">{name}</strong>. An enterprise solution engineer will follow up with you at <strong className="text-navy-950">{email}</strong> within our guaranteed SLA window.
              </p>
              <div className="pt-4">
                <button
                  onClick={() => {
                    setSubmitted(false);
                    setName('');
                    setEmail('');
                    setCompany('');
                    setMessage('');
                  }}
                  className="px-5 py-2.5 bg-navy-900 hover:bg-navy-800 text-white rounded-lg text-xs font-semibold transition"
                >
                  Send Another Inquiry
                </button>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <h2 className="text-lg font-bold text-navy-950">Submit an Inquiry</h2>
                <p className="text-xs text-platinum-500 mt-0.5">
                  Fill in your details below and our team will get back to you promptly.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1">
                    Your Full Name *
                  </label>
                  <input
                    type="text"
                    required
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g. Jane Doe"
                    className="w-full px-3.5 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-600 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1">
                    Work Email Address *
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="jane@company.com"
                    className="w-full px-3.5 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-600 transition"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1">
                    Organization / Company
                  </label>
                  <input
                    type="text"
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    placeholder="e.g. Acme Retail Brands"
                    className="w-full px-3.5 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-600 transition"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-navy-900 mb-1">
                    Inquiry Topic
                  </label>
                  <select
                    value={inquiryType}
                    onChange={(e) => setInquiryType(e.target.value)}
                    className="w-full px-3.5 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-600 bg-white transition"
                  >
                    <option value="ENTERPRISE_DEMO">Platform Demo & Architecture Review</option>
                    <option value="SECURITY_AUDIT">Ledger Security & Trigger Verification</option>
                    <option value="INTEGRATION_SUPPORT">FastAPI & Supabase Integration</option>
                    <option value="LLIRE_INTELLIGENCE">LLIRE Fraud Detection Benchmark</option>
                    <option value="OTHER">General Inquiry</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-navy-900 mb-1">
                  Message / Project Requirements *
                </label>
                <textarea
                  required
                  rows={4}
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Describe your loyalty ledger use case, transaction volume requirements, or technical questions..."
                  className="w-full px-3.5 py-2 text-xs border border-platinum-300 rounded-lg focus:outline-none focus:border-lavender-600 transition resize-none"
                />
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full sm:w-auto px-6 py-2.5 bg-navy-900 hover:bg-navy-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition shadow-sm"
              >
                {isSubmitting ? (
                  <>
                    <Send className="w-3.5 h-3.5 animate-spin" />
                    Transmitting Inquiry...
                  </>
                ) : (
                  <>
                    <Send className="w-3.5 h-3.5" />
                    Send Inquiry Message
                  </>
                )}
              </button>
            </form>
          )}
        </div>

        {/* Office & Operations Card (5 cols) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm">
            <h3 className="text-sm font-bold text-navy-950 mb-3 flex items-center gap-2">
              <MapPin className="w-4 h-4 text-lavender-600" />
              Engineering Headquarters
            </h3>
            <p className="text-xs text-platinum-600 leading-relaxed mb-4">
              LoyaltyOS Enterprise Systems Architecture<br />
              Financial Ledger & Fraud Intelligence Division<br />
              United States & Remote Global Infrastructure
            </p>
            <div className="space-y-2 text-xs pt-3 border-t border-platinum-200 text-platinum-700">
              <div className="flex items-center gap-2.5">
                <Mail className="w-3.5 h-3.5 text-platinum-400" />
                <span className="font-mono">contact@loyaltyos.internal</span>
              </div>
              <div className="flex items-center gap-2.5">
                <Clock className="w-3.5 h-3.5 text-platinum-400" />
                <span>Operating Hours: Monday – Friday, 08:00 – 18:00 UTC</span>
              </div>
            </div>
          </div>

          <div className="bg-lavender-50/70 border border-lavender-200 rounded-xl p-6">
            <h3 className="text-sm font-bold text-navy-950 mb-2 flex items-center gap-2">
              <FileText className="w-4 h-4 text-lavender-700" />
              Explore Platform Live
            </h3>
            <p className="text-xs text-platinum-700 leading-relaxed mb-4">
              You do not need to wait for a demo to test LoyaltyOS. The multi-persona operational workspace is available immediately for interactive exploration.
            </p>
            <Link
              to="/workspace"
              className="inline-flex items-center gap-2 text-xs font-semibold text-lavender-800 hover:text-lavender-900 group"
            >
              Open Interactive Workspace
              <ArrowRight className="w-3.5 h-3.5 transition group-hover:translate-x-0.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Direct Contact Channels Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {contactChannels.map((c, i) => (
          <div key={i} className="bg-white border border-platinum-200 rounded-xl p-6 shadow-sm hover:border-lavender-200 transition">
            <div className="w-10 h-10 rounded-lg bg-platinum-100 flex items-center justify-center mb-3">
              {c.icon}
            </div>
            <h3 className="text-sm font-bold text-navy-950 mb-1">{c.title}</h3>
            <p className="text-xs text-platinum-600 leading-relaxed mb-4">{c.desc}</p>
            <div className="pt-3 border-t border-platinum-100 flex items-center justify-between text-[11px]">
              <span className="font-mono text-navy-900 font-semibold">{c.email}</span>
              <span className="text-emerald-700 font-medium bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                {c.sla}
              </span>
            </div>
          </div>
        ))}
      </div>
    </PageContainer>
  );
};
