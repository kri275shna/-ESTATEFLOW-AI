"use client";

import { useEffect, useState } from "react";
import { Building2, Sparkles, ShieldCheck, Calendar, ArrowRight, CheckCircle2, RefreshCw } from "lucide-react";

interface HealthStatus {
  status: string;
  service: string;
  version: string;
  database: string;
  client: string;
  location: string;
  ai_engine: string;
  timestamp: string;
}

export default function Home() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/health");
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setHealth(data);
    } catch (err: any) {
      setError(err.message || "Failed to reach backend API");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
      {/* Top Navigation */}
      <header className="sticky top-0 z-50 border-b border-[#EAEAE6] bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0F172A] text-white shadow-sm">
              <Building2 className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight text-[#0F172A]">EstateFlow AI</span>
              <span className="ml-2 rounded-md bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
                Ahmedabad MVP
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <a
              href="/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-[#475569] hover:bg-[#F1F5F9] transition"
            >
              Sign In
            </a>
            <a
              href="/chat"
              className="flex items-center gap-2 rounded-lg bg-[#0F172A] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-[#1E293B] transition"
            >
              <Sparkles className="h-4 w-4 text-emerald-400" />
              Buyer AI Concierge
            </a>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:py-20">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50/70 px-3 py-1 text-xs font-medium text-emerald-800 mb-6">
              <ShieldCheck className="h-3.5 w-3.5 text-emerald-600" />
              Company A • 420 Units • GujRERA Grounded
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-[#0F172A] sm:text-5xl lg:text-6xl">
              Next-generation residential lead intelligence.
            </h1>
            <p className="mt-6 text-lg text-[#475569] leading-relaxed">
              Empowering residential developers in Ahmedabad with sub-5-minute AI response times, 
              strict fact-sheet grounding, and transactional double-booking protection.
            </p>

            <div className="mt-8 flex flex-wrap gap-4">
              <a
                href="/chat"
                className="flex items-center gap-2 rounded-xl bg-[#059669] px-6 py-3.5 text-sm font-semibold text-white shadow-sm hover:bg-[#047857] transition"
              >
                Experience Buyer Chat
                <ArrowRight className="h-4 w-4" />
              </a>
              <a
                href="/leads"
                className="flex items-center gap-2 rounded-xl border border-[#CBD5E1] bg-white px-6 py-3.5 text-sm font-semibold text-[#0F172A] shadow-sm hover:bg-[#F8FAFC] transition"
              >
                Sales Pipeline & Leads
              </a>
              <a
                href="/admin"
                className="flex items-center gap-2 rounded-xl border border-[#CBD5E1] bg-white px-6 py-3.5 text-sm font-semibold text-[#0F172A] shadow-sm hover:bg-[#F8FAFC] transition"
              >
                Admin & Fact Sheet
              </a>
            </div>
          </div>

          {/* Backend Connectivity & Architecture Validation Card */}
          <div className="mt-16 rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#F1F5F9] pb-4">
              <div className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${health ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
                <h2 className="text-base font-semibold text-[#0F172A]">Foundation & Engine Connectivity</h2>
              </div>
              <button
                onClick={fetchHealth}
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg border border-[#E2E8F0] px-3 py-1.5 text-xs font-medium text-[#475569] hover:bg-[#F8FAFC] disabled:opacity-50 transition"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                Refresh
              </button>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-xl border border-[#F1F5F9] bg-[#FBFBFA] p-4">
                <span className="text-xs font-medium text-[#64748B]">Service Architecture</span>
                <p className="mt-1 text-sm font-bold text-[#0F172A]">{health?.service || "FastAPI 0.110+ & Next.js 14"}</p>
                <span className="text-[11px] text-[#94A3B8]">App Router + TypeScript</span>
              </div>

              <div className="rounded-xl border border-[#F1F5F9] bg-[#FBFBFA] p-4">
                <span className="text-xs font-medium text-[#64748B]">Database Engine</span>
                <div className="mt-1 flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <p className="text-sm font-bold text-[#0F172A] capitalize">{health?.database || "Active"}</p>
                </div>
                <span className="text-[11px] text-[#94A3B8]">SQLAlchemy 2.0 / ACID Locking</span>
              </div>

              <div className="rounded-xl border border-[#F1F5F9] bg-[#FBFBFA] p-4">
                <span className="text-xs font-medium text-[#64748B]">AI Concierge Engine</span>
                <p className="mt-1 text-xs font-bold text-[#0F172A] truncate">
                  {health?.ai_engine || "Fact-Sheet Grounded"}
                </p>
                <span className="text-[11px] text-[#94A3B8]">EN / HI / GU Multilingual</span>
              </div>

              <div className="rounded-xl border border-[#F1F5F9] bg-[#FBFBFA] p-4">
                <span className="text-xs font-medium text-[#64748B]">Client Deployment</span>
                <p className="mt-1 text-sm font-bold text-[#0F172A]">{health?.client || "Company A"}</p>
                <span className="text-[11px] text-[#94A3B8]">{health?.location || "Ahmedabad, Gujarat"}</span>
              </div>
            </div>

            {error && (
              <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs text-amber-800">
                <strong>Backend status:</strong> {error}. Start the backend via <code className="rounded bg-amber-100 px-1 py-0.5">uvicorn app.main:app --port 8000</code>.
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-[#EAEAE6] bg-white py-6 text-center text-xs text-[#64748B]">
        EstateFlow AI MVP • Developed for Residential Property Developer, Ahmedabad • Gujarat RERA Compliant
      </footer>
    </div>
  );
}
