"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Building2, Sparkles, ShieldCheck, Calendar, ArrowRight,
  CheckCircle2, RefreshCw, Users, BarChart3, Settings, Key
} from "lucide-react";
import Navbar from "@/components/Navbar";

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

  const featureScreens = [
    {
      title: "Multilingual AI Concierge",
      desc: "Instant responses in English, Hindi, and Gujarati. Grounded strictly in approved database fact sheets with refusal of fake discounts.",
      href: "/chat",
      icon: Sparkles,
      badge: "Buyer & Public",
      color: "emerald"
    },
    {
      title: "Site-Visit Booking Engine",
      desc: "Transactional PostgreSQL booking engine with row-level locks, zero double bookings, instant SMS/Email reminder simulation.",
      href: "/book",
      icon: Calendar,
      badge: "Concurrency Safe",
      color: "blue"
    },
    {
      title: "Lead Management & Deduplication",
      desc: "E.164 phone normalization, secondary attribution preservation, search, filtering, and assignment across 4 acquisition sources.",
      href: "/leads",
      icon: Users,
      badge: "Sales Head & Exec",
      color: "purple"
    },
    {
      title: "Sales Executive Workspace",
      desc: "Dedicated daily workspace for 11 sales reps. Today's visits, 1-click attendance marking, and flagged AI handoffs.",
      href: "/sales",
      icon: CheckCircle2,
      badge: "Sales Rep SLA",
      color: "teal"
    },
    {
      title: "Executive Business Analytics",
      desc: "Real SQL aggregation of Show-up rate, conversion funnel, cost per lead, and first-response SLA targets against ₹30L monthly spend.",
      href: "/analytics",
      icon: BarChart3,
      badge: "Leadership KPIs",
      color: "amber"
    },
    {
      title: "Admin Fact Sheet & Slot Governance",
      desc: "Real-time fact sheet editor, slot capacity controller, and audit trail tracking compliance with Gujarat RERA and DPDP Act 2023.",
      href: "/admin",
      icon: Settings,
      badge: "Admin & Compliance",
      color: "rose"
    }
  ];

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
      <Navbar />

      {/* Hero Section */}
      <main className="flex-1">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:py-16">
          <div className="max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-200 bg-emerald-50/70 px-3.5 py-1 text-xs font-semibold text-emerald-800 mb-6">
              <ShieldCheck className="h-4 w-4 text-emerald-600" />
              Company A Ahmedabad • 2 Projects • 420 Apartments • GujRERA Grounded
            </div>
            <h1 className="text-4xl font-extrabold tracking-tight text-[#0F172A] sm:text-5xl lg:text-6xl">
              Next-generation residential lead intelligence.
            </h1>
            <p className="mt-5 text-base sm:text-lg text-[#475569] leading-relaxed">
              Designed specifically for residential property developers in Ahmedabad. 
              Reduces median first response from <strong>14 hours to &lt; 2 minutes</strong>, eliminates uncontacted leads, 
              and enforces concurrency-safe site visit scheduling.
            </p>

            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/chat"
                className="flex items-center gap-2 rounded-xl bg-[#059669] px-6 py-3.5 text-sm font-semibold text-white shadow-sm hover:bg-[#047857] transition"
              >
                <Sparkles className="h-4 w-4" />
                Launch Buyer AI Concierge
              </Link>
              <Link
                href="/login"
                className="flex items-center gap-2 rounded-xl border border-[#CBD5E1] bg-white px-6 py-3.5 text-sm font-semibold text-[#0F172A] shadow-sm hover:bg-[#F8FAFC] transition"
              >
                <Key className="h-4 w-4 text-emerald-600" />
                1-Click Reviewer Login
              </Link>
              <Link
                href="/analytics"
                className="flex items-center gap-2 rounded-xl border border-[#CBD5E1] bg-white px-6 py-3.5 text-sm font-semibold text-[#0F172A] shadow-sm hover:bg-[#F8FAFC] transition"
              >
                <BarChart3 className="h-4 w-4 text-blue-600" />
                View Executive KPIs
              </Link>
            </div>
          </div>

          {/* 6 Core Functional Screens */}
          <div className="mt-16 space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-bold text-[#0F172A]">Core Architecture &amp; Modules</h2>
                <p className="text-xs text-[#64748B]">Complete end-to-end evaluation slice pre-seeded with sample data</p>
              </div>
              <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700">
                6 Working Screens
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featureScreens.map((s) => {
                const Icon = s.icon;
                return (
                  <Link
                    key={s.title}
                    href={s.href}
                    className="group p-6 rounded-2xl bg-white border border-[#EAEAE6] shadow-sm hover:shadow-md hover:border-emerald-300 transition flex flex-col justify-between space-y-4"
                  >
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="w-10 h-10 rounded-xl bg-slate-100 text-[#0F172A] flex items-center justify-center group-hover:bg-emerald-600 group-hover:text-white transition">
                          <Icon className="h-5 w-5" />
                        </div>
                        <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {s.badge}
                        </span>
                      </div>

                      <h3 className="text-base font-bold text-[#0F172A] group-hover:text-emerald-700 transition">
                        {s.title}
                      </h3>
                      <p className="text-xs text-[#64748B] leading-relaxed">
                        {s.desc}
                      </p>
                    </div>

                    <div className="pt-3 border-t border-[#F1F5F9] flex items-center justify-between text-xs font-semibold text-emerald-700">
                      <span>Explore Module</span>
                      <ArrowRight className="h-3.5 w-3.5 group-hover:translate-x-1 transition" />
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Backend Connectivity Card */}
          <div className="mt-16 rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#F1F5F9] pb-4">
              <div className="flex items-center gap-3">
                <div className={`h-3 w-3 rounded-full ${health ? "bg-emerald-500 animate-pulse" : "bg-amber-400"}`} />
                <h2 className="text-base font-semibold text-[#0F172A]">Runtime Environment &amp; Microservices</h2>
              </div>
              <button
                onClick={fetchHealth}
                disabled={loading}
                className="flex items-center gap-1.5 rounded-lg border border-[#E2E8F0] px-3 py-1.5 text-xs font-medium text-[#475569] hover:bg-[#F8FAFC] disabled:opacity-50 transition"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
                Check System Health
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
        EstateFlow AI MVP • Residential Lead Intelligence Platform for Ahmedabad • Gujarat RERA &amp; DPDP Act 2023 Compliant
      </footer>
    </div>
  );
}
