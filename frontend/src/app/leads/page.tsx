"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { getStoredToken, getStoredUser, AuthUser } from "@/lib/auth";
import { formatINR, formatDateTime } from "@/lib/utils";
import { 
  Search, Filter, Plus, ChevronLeft, ChevronRight, UserPlus, 
  ExternalLink, Layers, AlertTriangle, CheckCircle2, ShieldAlert,
  Phone, Calendar, ArrowUpDown, Loader2
} from "lucide-react";

interface LeadItem {
  id: string;
  lead_reference: string;
  full_name: string;
  normalized_phone: string;
  raw_phone: string;
  email?: string;
  source: string;
  duplicate_sources: string[];
  preferred_project_name?: string;
  preferred_bhk?: string;
  budget_min?: number;
  budget_max?: number;
  buying_timeline?: string;
  status: string;
  qualification_score: number;
  is_qualified: boolean;
  assigned_executive_id?: string;
  assigned_executive_name?: string;
  created_at: string;
}

interface ExecutiveItem {
  id: string;
  full_name: string;
  role: string;
}

export default function LeadsPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [leads, setLeads] = useState<LeadItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("ALL");
  const [statusFilter, setStatusFilter] = useState("ALL");
  
  // Executives for assignment
  const [executives, setExecutives] = useState<ExecutiveItem[]>([]);
  const [assigningId, setAssigningId] = useState<string | null>(null);

  // New Lead Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [newLeadForm, setNewLeadForm] = useState({
    full_name: "",
    raw_phone: "",
    email: "",
    source: "Property portal",
    preferred_bhk: "3 BHK",
    budget_min: "8500000",
    budget_max: "9500000",
    buying_timeline: "Immediate (0-1 mo)",
  });
  const [modalFeedback, setModalFeedback] = useState<{ message: string; isDup: boolean } | null>(null);
  const [modalLoading, setModalLoading] = useState(false);

  // Load leads
  const fetchLeads = useCallback(async () => {
    const token = getStoredToken();
    if (!token) {
      router.push("/login");
      return;
    }

    setLoading(true);
    setError(null);

    const params = new URLSearchParams();
    if (search.trim()) params.append("search", search.trim());
    if (source !== "ALL") params.append("source", source);
    if (statusFilter !== "ALL") params.append("status", statusFilter);
    params.append("page", page.toString());
    params.append("page_size", "12");

    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        if (res.status === 401) {
          router.push("/login");
          return;
        }
        throw new Error(`Failed to load leads (${res.status})`);
      }

      const data = await res.json();
      setLeads(data.leads);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err: any) {
      setError(err.message || "Failed to load leads");
    } finally {
      setLoading(false);
    }
  }, [page, search, source, statusFilter, router]);

  // Load executives for assignment
  const fetchExecutives = async () => {
    const token = getStoredToken();
    if (!token) return;
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/demo-users", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const users = await res.json();
        setExecutives(users.filter((u: any) => u.role === "SALES_EXECUTIVE"));
      }
    } catch {}
  };

  useEffect(() => {
    const user = getStoredUser();
    if (!user) {
      router.push("/login");
      return;
    }
    setCurrentUser(user);
    fetchLeads();
    fetchExecutives();
  }, [fetchLeads, router]);

  // Handle lead assignment
  const handleAssign = async (leadId: string, execId: string) => {
    const token = getStoredToken();
    if (!token) return;
    setAssigningId(leadId);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads/${leadId}/assign`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ assigned_executive_id: execId }),
      });
      if (res.ok) {
        fetchLeads();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setAssigningId(null);
    }
  };

  // Handle add lead form
  const handleCreateLead = async (e: React.FormEvent) => {
    e.preventDefault();
    setModalLoading(true);
    setModalFeedback(null);

    try {
      const res = await fetch("http://localhost:8000/api/v1/leads", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ...newLeadForm,
          budget_min: parseFloat(newLeadForm.budget_min),
          budget_max: parseFloat(newLeadForm.budget_max),
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Validation error creating lead");
      }

      const data = await res.json();
      if (data.is_duplicate) {
        setModalFeedback({
          message: `Duplicate buyer detected for ${data.lead.normalized_phone}! Added '${newLeadForm.source}' to attribution history without duplicating record.`,
          isDup: true,
        });
      } else {
        setModalFeedback({
          message: `New lead created successfully! Assigned ID: ${data.lead.lead_reference}`,
          isDup: false,
        });
      }
      fetchLeads();
    } catch (err: any) {
      setModalFeedback({ message: err.message, isDup: false });
    } finally {
      setModalLoading(false);
    }
  };

  // Helper badge styles
  const getStatusBadge = (status: string) => {
    switch (status) {
      case "VISIT_BOOKED":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "VISITED":
        return "bg-teal-100 text-teal-800 border-teal-300";
      case "QUALIFIED":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "CONTACTED":
        return "bg-indigo-100 text-indigo-800 border-indigo-300";
      case "HUMAN_FOLLOWUP":
        return "bg-amber-100 text-amber-800 border-amber-300 animate-pulse";
      case "LOST":
      case "NOT_INTERESTED":
        return "bg-rose-100 text-rose-800 border-rose-300";
      default:
        return "bg-slate-100 text-slate-800 border-slate-300";
    }
  };

  const getSourceBadge = (sourceName: string) => {
    switch (sourceName) {
      case "Property portal":
        return "bg-sky-50 text-sky-700 border-sky-200";
      case "Social media":
      case "Social media ad":
        return "bg-purple-50 text-purple-700 border-purple-200";
      case "Hoarding":
      case "Hoarding call":
        return "bg-amber-50 text-amber-700 border-amber-200";
      default:
        return "bg-emerald-50 text-emerald-700 border-emerald-200";
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
      <Navbar />

      <main className="flex-1 mx-auto max-w-7xl w-full px-6 py-8">
        {/* Top Header & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#EAEAE6] pb-6">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Centralized Lead Management</h1>
              <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                {total} Total Leads
              </span>
            </div>
            <p className="mt-1 text-xs text-[#64748B]">
              Integrated pipeline from property portals, social ads, hoardings, and organic web with automated phone deduplication.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => {
                setShowAddModal(true);
                setModalFeedback(null);
              }}
              className="flex items-center gap-2 rounded-xl bg-[#0F172A] px-4 py-2 text-xs font-semibold text-white shadow-sm hover:bg-[#1E293B] transition"
            >
              <Plus className="h-4 w-4 text-emerald-400" />
              Ingest Enquiry / Lead
            </button>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {/* Search Box */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
            <input
              type="text"
              placeholder="Search name, phone, or LD-ID..."
              value={search}
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-xl border border-[#CBD5E1] bg-white py-2 pl-9 pr-4 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            />
          </div>

          {/* Source Filter */}
          <div>
            <select
              value={source}
              onChange={(e) => {
                setSource(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
            >
              <option value="ALL">All Sources</option>
              <option value="Property portal">Property portal (99acres/MagicBricks)</option>
              <option value="Social media">Social media ad</option>
              <option value="Hoarding">Hoarding call</option>
              <option value="Website">Organic Website</option>
              <option value="Manual entry">Manual Entry</option>
            </select>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="NEW">NEW</option>
              <option value="CONTACTED">CONTACTED</option>
              <option value="QUALIFIED">QUALIFIED</option>
              <option value="VISIT_BOOKED">VISIT_BOOKED</option>
              <option value="VISITED">VISITED</option>
              <option value="HUMAN_FOLLOWUP">HUMAN_FOLLOWUP</option>
              <option value="NOT_INTERESTED">NOT_INTERESTED</option>
              <option value="LOST">LOST</option>
            </select>
          </div>

          {/* Reset Filters */}
          <button
            onClick={() => {
              setSearch("");
              setSource("ALL");
              setStatusFilter("ALL");
              setPage(1);
            }}
            className="flex items-center justify-center gap-1.5 rounded-xl border border-[#E2E8F0] bg-white py-2 px-3 text-xs font-medium text-[#475569] hover:bg-[#F8FAFC] transition"
          >
            <Filter className="h-3.5 w-3.5" />
            Clear Filters
          </button>
        </div>

        {/* Leads Table */}
        <div className="mt-6 overflow-hidden rounded-2xl border border-[#EAEAE6] bg-white shadow-sm">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
              <span className="ml-2 text-xs font-medium text-[#64748B]">Loading leads...</span>
            </div>
          ) : error ? (
            <div className="p-8 text-center">
              <AlertTriangle className="mx-auto h-8 w-8 text-rose-500" />
              <p className="mt-2 text-xs font-semibold text-rose-700">{error}</p>
            </div>
          ) : leads.length === 0 ? (
            <div className="p-12 text-center">
              <Layers className="mx-auto h-10 w-10 text-[#94A3B8]" />
              <p className="mt-3 text-sm font-semibold text-[#0F172A]">No leads matching criteria</p>
              <p className="mt-1 text-xs text-[#64748B]">Try resetting your search query or source filters.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-[#F1F5F9] bg-[#F8FAFC] text-[11px] font-bold uppercase tracking-wider text-[#64748B]">
                    <th className="py-3 px-4">Lead ID</th>
                    <th className="py-3 px-4">Buyer Details</th>
                    <th className="py-3 px-4">Project & Config</th>
                    <th className="py-3 px-4">Budget (INR)</th>
                    <th className="py-3 px-4">Source Channel</th>
                    <th className="py-3 px-4">Status</th>
                    <th className="py-3 px-4">Score</th>
                    <th className="py-3 px-4">Assigned Salesperson</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#F1F5F9] text-xs">
                  {leads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-[#FBFBFA] transition">
                      {/* ID + Duplicate flag */}
                      <td className="py-3.5 px-4 whitespace-nowrap font-mono text-[11px] font-bold text-[#0F172A]">
                        <div className="flex items-center gap-1.5">
                          <span>{lead.lead_reference}</span>
                          {lead.duplicate_sources && lead.duplicate_sources.length > 0 && (
                            <span 
                              title={`Multi-channel arrival: ${lead.duplicate_sources.join(", ")}`}
                              className="inline-flex items-center rounded bg-amber-100 px-1 py-0.5 text-[9px] font-bold text-amber-800 border border-amber-300"
                            >
                              +{lead.duplicate_sources.length} Dup
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Name & Phone */}
                      <td className="py-3.5 px-4">
                        <div className="font-semibold text-[#0F172A]">{lead.full_name}</div>
                        <div className="flex items-center gap-1 text-[11px] text-[#64748B]">
                          <Phone className="h-3 w-3 text-slate-400" />
                          <span>{lead.normalized_phone}</span>
                        </div>
                      </td>

                      {/* Project & BHK */}
                      <td className="py-3.5 px-4">
                        <div className="font-medium text-[#0F172A]">{lead.preferred_project_name || "Any Project"}</div>
                        <div className="text-[11px] text-emerald-700 font-semibold">{lead.preferred_bhk || "-"}</div>
                      </td>

                      {/* Budget */}
                      <td className="py-3.5 px-4 whitespace-nowrap font-medium text-[#334155]">
                        {lead.budget_min ? `${formatINR(lead.budget_min)} - ${formatINR(lead.budget_max || lead.budget_min)}` : "Not specified"}
                      </td>

                      {/* Source */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`inline-block rounded-md border px-2 py-0.5 text-[10px] font-semibold ${getSourceBadge(lead.source)}`}>
                          {lead.source}
                        </span>
                      </td>

                      {/* Status */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <span className={`inline-block rounded-md border px-2 py-0.5 text-[10px] font-bold ${getStatusBadge(lead.status)}`}>
                          {lead.status.replace("_", " ")}
                        </span>
                      </td>

                      {/* Score */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        <div className="flex items-center gap-1.5">
                          <div className="w-10 bg-slate-200 h-1.5 rounded-full overflow-hidden">
                            <div 
                              className={`h-full ${lead.qualification_score >= 80 ? "bg-emerald-500" : lead.qualification_score >= 50 ? "bg-blue-500" : "bg-amber-500"}`}
                              style={{ width: `${lead.qualification_score}%` }}
                            />
                          </div>
                          <span className="text-[11px] font-bold text-[#0F172A]">{lead.qualification_score}</span>
                        </div>
                      </td>

                      {/* Assigned Executive */}
                      <td className="py-3.5 px-4 whitespace-nowrap">
                        {(currentUser?.role === "ADMIN" || currentUser?.role === "SALES_HEAD") ? (
                          <select
                            value={lead.assigned_executive_id || ""}
                            onChange={(e) => handleAssign(lead.id, e.target.value)}
                            disabled={assigningId === lead.id}
                            className="rounded-lg border border-[#E2E8F0] bg-white py-1 px-2 text-[11px] text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                          >
                            <option value="">Unassigned</option>
                            {executives.map((ex) => (
                              <option key={ex.id} value={ex.id}>
                                {ex.full_name}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <span className="text-xs text-[#334155]">{lead.assigned_executive_name}</span>
                        )}
                      </td>

                      {/* View Action */}
                      <td className="py-3.5 px-4 text-right whitespace-nowrap">
                        <a
                          href={`/leads/${lead.id}`}
                          className="inline-flex items-center gap-1 rounded-lg border border-[#E2E8F0] bg-white px-2.5 py-1 text-[11px] font-semibold text-[#0F172A] hover:bg-[#F1F5F9] transition"
                        >
                          Dossier
                          <ExternalLink className="h-3 w-3 text-[#64748B]" />
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination Footer */}
          <div className="flex items-center justify-between border-t border-[#F1F5F9] bg-[#F8FAFC] px-6 py-3 text-xs text-[#64748B]">
            <div>
              Showing page <span className="font-bold text-[#0F172A]">{page}</span> of{" "}
              <span className="font-bold text-[#0F172A]">{totalPages}</span> ({total} leads)
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="flex items-center gap-1 rounded-lg border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-medium text-[#0F172A] hover:bg-[#F8FAFC] disabled:opacity-40 transition"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                Previous
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page >= totalPages}
                className="flex items-center gap-1 rounded-lg border border-[#E2E8F0] bg-white px-3 py-1.5 text-xs font-medium text-[#0F172A] hover:bg-[#F8FAFC] disabled:opacity-40 transition"
              >
                Next
                <ChevronRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Modal: Ingest New Enquiry with Duplicate Check */}
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-xl">
              <div className="flex items-center justify-between border-b border-[#F1F5F9] pb-3">
                <h3 className="text-base font-bold text-[#0F172A]">Ingest Incoming Property Enquiry</h3>
                <button
                  onClick={() => setShowAddModal(false)}
                  className="rounded-lg p-1 text-[#94A3B8] hover:bg-[#F1F5F9] hover:text-[#0F172A]"
                >
                  ✕
                </button>
              </div>

              {modalFeedback && (
                <div className={`mt-4 rounded-xl border p-3.5 text-xs ${modalFeedback.isDup ? "border-amber-200 bg-amber-50 text-amber-900" : "border-emerald-200 bg-emerald-50 text-emerald-900"}`}>
                  <div className="flex items-start gap-2">
                    {modalFeedback.isDup ? <AlertTriangle className="h-4 w-4 shrink-0 text-amber-600 mt-0.5" /> : <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-600 mt-0.5" />}
                    <span>{modalFeedback.message}</span>
                  </div>
                </div>
              )}

              <form onSubmit={handleCreateLead} className="mt-4 space-y-3.5">
                <div>
                  <label className="block text-xs font-medium text-[#334155]">Full Name *</label>
                  <input
                    type="text"
                    required
                    value={newLeadForm.full_name}
                    onChange={(e) => setNewLeadForm({ ...newLeadForm, full_name: e.target.value })}
                    placeholder="e.g. Ramesh Patel"
                    className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[#334155]">Phone Number *</label>
                    <input
                      type="text"
                      required
                      value={newLeadForm.raw_phone}
                      onChange={(e) => setNewLeadForm({ ...newLeadForm, raw_phone: e.target.value })}
                      placeholder="e.g. 98251 00000"
                      className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#334155]">Channel Source</label>
                    <select
                      value={newLeadForm.source}
                      onChange={(e) => setNewLeadForm({ ...newLeadForm, source: e.target.value })}
                      className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    >
                      <option value="Property portal">Property portal</option>
                      <option value="Social media">Social media ad</option>
                      <option value="Hoarding">Hoarding call</option>
                      <option value="Website">Organic Website</option>
                      <option value="Manual entry">Manual Telecaller Entry</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[#334155]">Configuration</label>
                    <select
                      value={newLeadForm.preferred_bhk}
                      onChange={(e) => setNewLeadForm({ ...newLeadForm, preferred_bhk: e.target.value })}
                      className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    >
                      <option value="2 BHK">2 BHK</option>
                      <option value="3 BHK">3 BHK</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#334155]">Buying Timeline</label>
                    <select
                      value={newLeadForm.buying_timeline}
                      onChange={(e) => setNewLeadForm({ ...newLeadForm, buying_timeline: e.target.value })}
                      className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    >
                      <option value="Immediate (0-1 mo)">Immediate (0-1 mo)</option>
                      <option value="1-3 months">1-3 months</option>
                      <option value="3-6 months">3-6 months</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-[#334155]">Min Budget (INR)</label>
                    <input
                      type="number"
                      value={newLeadForm.budget_min}
                      onChange={(e) => setNewLeadForm({ ...newLeadForm, budget_min: e.target.value })}
                      className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-[#334155]">Max Budget (INR)</label>
                    <input
                      type="number"
                      value={newLeadForm.budget_max}
                      onChange={(e) => setNewLeadForm({ ...newLeadForm, budget_max: e.target.value })}
                      className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    />
                  </div>
                </div>

                <div className="mt-5 flex justify-end gap-2 border-t border-[#F1F5F9] pt-3">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="rounded-xl border border-[#E2E8F0] px-4 py-2 text-xs font-medium text-[#475569] hover:bg-[#F8FAFC]"
                  >
                    Close
                  </button>
                  <button
                    type="submit"
                    disabled={modalLoading}
                    className="flex items-center gap-1.5 rounded-xl bg-[#0F172A] px-4 py-2 text-xs font-semibold text-white hover:bg-[#1E293B] disabled:opacity-50"
                  >
                    {modalLoading && <Loader2 className="h-3.5 w-3.5 animate-spin text-emerald-400" />}
                    Submit & Check Duplicate
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
