"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { Building2, Sparkles, Calendar, Users, BarChart3, Settings, LogOut, ShieldCheck, CheckCircle } from "lucide-react";
import { getStoredUser, clearAuthSession, AuthUser } from "@/lib/auth";

export default function Navbar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  const handleLogout = () => {
    clearAuthSession();
    router.push("/login");
  };

  const navLinks = [
    { name: "Buyer AI Concierge", href: "/chat", icon: Sparkles, public: true },
    { name: "Site Visits", href: "/book", icon: Calendar, public: true },
    { name: "Lead Pipeline", href: "/leads", icon: Users, roles: ["SALES_HEAD", "ADMIN", "SALES_EXECUTIVE"] },
    { name: "My Workspace", href: "/sales", icon: CheckCircle, roles: ["SALES_EXECUTIVE"] },
    { name: "Analytics & KPIs", href: "/analytics", icon: BarChart3, roles: ["SALES_HEAD", "ADMIN"] },
    { name: "Admin Config", href: "/admin", icon: Settings, roles: ["ADMIN", "SALES_HEAD"] },
  ];

  const visibleLinks = navLinks.filter((item) => {
    if (item.public) return true;
    if (!user) return false;
    return item.roles?.includes(user.role);
  });

  return (
    <header className="sticky top-0 z-50 border-b border-[#EAEAE6] bg-white/90 backdrop-blur-md">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5">
        <div className="flex items-center gap-6">
          <a href="/" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#0F172A] text-white">
              <Building2 className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <span className="text-base font-bold tracking-tight text-[#0F172A]">EstateFlow AI</span>
              <span className="hidden sm:inline-block ml-2 rounded bg-emerald-50 px-1.5 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                Ahmedabad
              </span>
            </div>
          </a>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            {visibleLinks.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
              return (
                <a
                  key={item.name}
                  href={item.href}
                  className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                    isActive
                      ? "bg-[#0F172A] text-white shadow-sm"
                      : "text-[#475569] hover:bg-[#F1F5F9] hover:text-[#0F172A]"
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? "text-emerald-400" : "text-[#64748B]"}`} />
                  {item.name}
                </a>
              );
            })}
          </nav>
        </div>

        {/* Right User State */}
        <div className="flex items-center gap-3">
          {user ? (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex flex-col text-right">
                <span className="text-xs font-bold text-[#0F172A]">{user.full_name}</span>
                <span className="text-[10px] font-semibold text-emerald-700 uppercase tracking-wider">
                  {user.role.replace("_", " ")}
                </span>
              </div>
              <button
                onClick={handleLogout}
                title="Sign out"
                className="flex items-center gap-1.5 rounded-lg border border-[#E2E8F0] px-2.5 py-1.5 text-xs font-medium text-[#64748B] hover:bg-[#F8FAFC] hover:text-red-600 transition"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Logout</span>
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <a
                href="/login"
                className="rounded-lg px-3 py-1.5 text-xs font-semibold text-[#475569] hover:bg-[#F1F5F9] transition"
              >
                Sign In
              </a>
              <a
                href="/chat"
                className="flex items-center gap-1.5 rounded-lg bg-[#0F172A] px-3.5 py-1.5 text-xs font-semibold text-white hover:bg-[#1E293B] transition"
              >
                <Sparkles className="h-3.5 w-3.5 text-emerald-400" />
                Buyer Chat
              </a>
            </div>
          )}
        </div>
      </div>

      {/* Mobile Links */}
      <div className="flex md:hidden overflow-x-auto border-t border-[#F1F5F9] px-4 py-2 gap-1">
        {visibleLinks.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href;
          return (
            <a
              key={item.name}
              href={item.href}
              className={`flex shrink-0 items-center gap-1 rounded-md px-2.5 py-1 text-[11px] font-medium ${
                isActive ? "bg-[#0F172A] text-white" : "text-[#475569]"
              }`}
            >
              <Icon className="h-3 w-3" />
              {item.name}
            </a>
          );
        })}
      </div>
    </header>
  );
}
