"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Building2, ShieldCheck, Lock, Mail, ArrowRight, Loader2, UserCheck, AlertCircle } from "lucide-react";
import { setAuthSession, AuthUser } from "@/lib/auth";

const DEMO_PRESETS = [
  {
    role: "ADMIN",
    title: "Administrator / Director",
    name: "Rajesh Parekh",
    email: "admin@estateflow.ai",
    pass: "Admin@123",
    badge: "Full Admin + Fact Sheet Control",
    redirect: "/admin",
  },
  {
    role: "SALES_HEAD",
    title: "Sales Head",
    name: "Bhavin Shah",
    email: "saleshead@estateflow.ai",
    pass: "Head@123",
    badge: "All Leads + Escalations + Analytics",
    redirect: "/leads",
  },
  {
    role: "SALES_EXECUTIVE",
    title: "Sales Executive",
    name: "Rahul Sharma",
    email: "rahul.sales@estateflow.ai",
    pass: "Sales@123",
    badge: "Assigned Leads + Site Visits",
    redirect: "/sales",
  },
  {
    role: "BUYER",
    title: "Prospective Buyer",
    name: "Gaurav Mehta",
    email: "buyer@estateflow.ai",
    pass: "Buyer@123",
    badge: "AI Concierge & Visit Booking",
    redirect: "/chat",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@estateflow.ai");
  const [password, setPassword] = useState("Admin@123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent, customEmail?: string, customPass?: string, redirectPath?: string) => {
    if (e) e.preventDefault();
    setError(null);
    setLoading(true);

    const loginEmail = customEmail || email;
    const loginPass = customPass || password;

    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: loginEmail, password: loginPass }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || "Authentication failed. Please verify credentials.");
      }

      const data = await res.json();
      const user: AuthUser = {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
      };

      setAuthSession(data.access_token, user);

      // Navigate based on role
      if (redirectPath) {
        router.push(redirectPath);
      } else if (data.role === "ADMIN") {
        router.push("/admin");
      } else if (data.role === "SALES_HEAD") {
        router.push("/leads");
      } else if (data.role === "SALES_EXECUTIVE") {
        router.push("/sales");
      } else {
        router.push("/chat");
      }
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickPreset = (preset: typeof DEMO_PRESETS[0]) => {
    setEmail(preset.email);
    setPassword(preset.pass);
    handleLogin(undefined, preset.email, preset.pass, preset.redirect);
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
      {/* Top Header */}
      <header className="border-b border-[#EAEAE6] bg-white px-6 py-4">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <a href="/" className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#0F172A] text-white">
              <Building2 className="h-5 w-5 text-emerald-400" />
            </div>
            <span className="text-lg font-bold tracking-tight text-[#0F172A]">EstateFlow AI</span>
          </a>
          <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 border border-emerald-200">
            Company A • Ahmedabad
          </span>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex flex-1 items-center justify-center px-4 py-12">
        <div className="w-full max-w-xl">
          <div className="rounded-2xl border border-[#EAEAE6] bg-white p-8 shadow-sm">
            <div className="text-center">
              <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Sign in to EstateFlow</h1>
              <p className="mt-2 text-sm text-[#64748B]">
                Role-based access control for developers, sales teams, and buyers.
              </p>
            </div>

            {error && (
              <div className="mt-6 flex items-center gap-2 rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-800">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-600" />
                <span>{error}</span>
              </div>
            )}

            {/* Quick Demo Switcher */}
            <div className="mt-6">
              <label className="text-xs font-semibold uppercase tracking-wider text-[#94A3B8]">
                One-Click Reviewer Demo Login
              </label>
              <div className="mt-2 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                {DEMO_PRESETS.map((p) => (
                  <button
                    key={p.role}
                    type="button"
                    onClick={() => handleQuickPreset(p)}
                    disabled={loading}
                    className="flex flex-col items-start rounded-xl border border-[#E2E8F0] bg-[#F8FAFC] p-3 text-left transition hover:border-emerald-500 hover:bg-emerald-50/40 disabled:opacity-50"
                  >
                    <div className="flex w-full items-center justify-between">
                      <span className="text-xs font-bold text-[#0F172A]">{p.title}</span>
                      <span className="text-[10px] font-semibold text-emerald-700">{p.role.replace("_", " ")}</span>
                    </div>
                    <span className="mt-0.5 text-xs text-[#64748B]">{p.name}</span>
                    <span className="mt-2 text-[10px] text-[#94A3B8]">{p.badge}</span>
                  </button>
                ))}
              </div>
            </div>

            <div className="relative my-6 text-center">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#EAEAE6]" />
              </div>
              <span className="relative bg-white px-3 text-xs font-medium text-[#94A3B8]">or sign in manually</span>
            </div>

            {/* Manual Form */}
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#334155]">Email Address</label>
                <div className="relative mt-1">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="name@estateflow.ai"
                    className="w-full rounded-xl border border-[#CBD5E1] bg-white py-2.5 pl-10 pr-4 text-sm text-[#0F172A] placeholder-[#94A3B8] focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-[#334155]">Password</label>
                <div className="relative mt-1">
                  <Lock className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full rounded-xl border border-[#CBD5E1] bg-white py-2.5 pl-10 pr-4 text-sm text-[#0F172A] placeholder-[#94A3B8] focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl bg-[#0F172A] py-3 text-sm font-semibold text-white shadow-sm hover:bg-[#1E293B] disabled:opacity-50 transition"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-emerald-400" />
                    Authenticating...
                  </>
                ) : (
                  <>
                    Sign In to Workspace
                    <ArrowRight className="h-4 w-4" />
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
}
