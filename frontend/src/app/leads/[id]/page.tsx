"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Navbar from "@/components/Navbar";
import { getStoredToken, getStoredUser, AuthUser } from "@/lib/auth";
import { formatINR, formatDateTime } from "@/lib/utils";
import {
  ChevronLeft, Phone, Mail, Building, Calendar, ShieldCheck, 
  Sparkles, CheckCircle2, Clock, AlertTriangle, MessageSquare, 
  User, Send, Loader2, ArrowRight
} from "lucide-react";

interface LeadDetail {
  id: string;
  lead_reference: string;
  full_name: string;
  normalized_phone: string;
  raw_phone: string;
  email?: string;
  source: string;
  duplicate_sources: string[];
  preferred_project_id?: string;
  preferred_project_name?: string;
  preferred_bhk?: string;
  budget_min?: number;
  budget_max?: number;
  preferred_location?: string;
  buying_timeline?: string;
  status: string;
  qualification_score: number;
  is_qualified: boolean;
  assigned_executive_id?: string;
  assigned_executive_name?: string;
  consent_status: boolean;
  first_contact_at?: string;
  last_contact_at?: string;
  created_at: string;
  conversations: Array<{
    id: string;
    session_token: string;
    preferred_language: string;
    is_flagged: boolean;
    flagged_reason?: string;
    messages: Array<{
      id: string;
      sender_type: string;
      content: string;
      language: string;
      is_uncertain: boolean;
      created_at: string;
    }>;
  }>;
  bookings: Array<{
    id: string;
    booking_reference: string;
    project_name: string;
    slot_start: string;
    slot_end: string;
    status: string;
    notes?: string;
    confirmed_at: string;
  }>;
  handoffs: Array<{
    id: string;
    reason: string;
    priority: string;
    structured_summary: string;
    recommended_action?: string;
    status: string;
    created_at: string;
  }>;
}

export default function LeadDetailPage() {
  const router = useRouter();
  const params = useParams();
  const leadId = params?.id as string;

  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusUpdateLoading, setStatusUpdateLoading] = useState(false);

  const fetchLeadDetails = async () => {
    const token = getStoredToken();
    if (!token) {
      router.push("/login");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads/${leadId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        if (res.status === 401) {
          router.push("/login");
          return;
        }
        throw new Error(`Failed to load lead (${res.status})`);
      }

      const data = await res.json();
      setLead(data);
    } catch (err: any) {
      setError(err.message || "Failed to load lead details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (leadId) {
      fetchLeadDetails();
    }
  }, [leadId]);

  const handleStatusChange = async (newStatus: string) => {
    const token = getStoredToken();
    if (!token || !lead) return;
    setStatusUpdateLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/leads/${lead.id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ status: newStatus }),
      });

      if (res.ok) {
        setLead({ ...lead, status: newStatus });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setStatusUpdateLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
        <Navbar />
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-emerald-600" />
          <span className="ml-2 text-xs font-medium text-[#64748B]">Loading dossier...</span>
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
        <Navbar />
        <div className="mx-auto max-w-xl py-16 px-4 text-center">
          <AlertTriangle className="mx-auto h-8 w-8 text-rose-500" />
          <h2 className="mt-2 text-base font-bold text-[#0F172A]">{error || "Lead Not Found"}</h2>
          <a
            href="/leads"
            className="mt-4 inline-flex items-center gap-1.5 rounded-xl bg-[#0F172A] px-4 py-2 text-xs font-semibold text-white"
          >
            <ChevronLeft className="h-4 w-4" />
            Back to Pipeline
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
      <Navbar />

      <main className="flex-1 mx-auto max-w-7xl w-full px-6 py-8">
        {/* Navigation Breadcrumb */}
        <div className="mb-6 flex items-center justify-between">
          <a
            href="/leads"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#64748B] hover:text-[#0F172A] transition"
          >
            <ChevronLeft className="h-4 w-4" />
            Back to Leads Pipeline
          </a>

          <div className="flex items-center gap-2">
            <span className="text-xs text-[#64748B]">Lead Status:</span>
            <select
              value={lead.status}
              disabled={statusUpdateLoading}
              onChange={(e) => handleStatusChange(e.target.value)}
              className="rounded-lg border border-[#CBD5E1] bg-white py-1 px-2.5 text-xs font-bold text-[#0F172A] focus:border-emerald-600 focus:outline-none"
            >
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
        </div>

        {/* Dossier Header Card */}
        <div className="rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#F1F5F9] pb-6">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-800 font-bold text-xl border border-emerald-200">
                {lead.full_name.charAt(0)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h1 className="text-xl font-bold text-[#0F172A]">{lead.full_name}</h1>
                  <span className="font-mono text-xs font-bold text-[#64748B] bg-slate-100 px-2 py-0.5 rounded">
                    {lead.lead_reference}
                  </span>
                  {lead.consent_status && (
                    <span className="inline-flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-800 border border-emerald-200">
                      <ShieldCheck className="h-3 w-3 text-emerald-600" />
                      DPDP Opt-In Verified
                    </span>
                  )}
                </div>

                <div className="mt-2 flex flex-wrap items-center gap-4 text-xs text-[#64748B]">
                  <div className="flex items-center gap-1.5">
                    <Phone className="h-3.5 w-3.5 text-slate-400" />
                    <span className="font-semibold text-[#0F172A]">{lead.normalized_phone}</span>
                    {lead.raw_phone !== lead.normalized_phone && (
                      <span className="text-[10px] text-slate-400">(raw: {lead.raw_phone})</span>
                    )}
                  </div>
                  {lead.email && (
                    <div className="flex items-center gap-1.5">
                      <Mail className="h-3.5 w-3.5 text-slate-400" />
                      <span>{lead.email}</span>
                    </div>
                  )}
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-slate-400" />
                    <span>Captured: {formatDateTime(lead.created_at)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Score & Attribution */}
            <div className="flex items-center gap-4">
              <div className="rounded-xl border border-[#F1F5F9] bg-[#F8FAFC] p-3 text-center min-w-[120px]">
                <span className="text-[10px] font-bold uppercase text-[#64748B]">Qualification</span>
                <div className="mt-0.5 text-2xl font-extrabold text-[#0F172A]">{lead.qualification_score}<span className="text-xs text-[#94A3B8]">/100</span></div>
                <span className={`text-[10px] font-bold ${lead.is_qualified ? "text-emerald-700" : "text-amber-700"}`}>
                  {lead.is_qualified ? "High Intent" : "Unqualified"}
                </span>
              </div>

              <div className="rounded-xl border border-[#F1F5F9] bg-[#F8FAFC] p-3 text-center min-w-[140px]">
                <span className="text-[10px] font-bold uppercase text-[#64748B]">Primary Source</span>
                <div className="mt-1 text-xs font-bold text-[#0F172A]">{lead.source}</div>
                {lead.duplicate_sources && lead.duplicate_sources.length > 0 && (
                  <span className="text-[9px] text-amber-800 font-semibold">
                    +{lead.duplicate_sources.length} re-inquiries merged
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Quick Metrics Strip */}
          <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="rounded-xl border border-[#F1F5F9] p-3 bg-[#FBFBFA]">
              <span className="text-[#94A3B8] font-medium">Interested Project</span>
              <p className="mt-1 font-bold text-[#0F172A]">{lead.preferred_project_name || "Harmony Enclave"}</p>
            </div>
            <div className="rounded-xl border border-[#F1F5F9] p-3 bg-[#FBFBFA]">
              <span className="text-[#94A3B8] font-medium">Configuration</span>
              <p className="mt-1 font-bold text-emerald-800">{lead.preferred_bhk || "2 BHK & 3 BHK"}</p>
            </div>
            <div className="rounded-xl border border-[#F1F5F9] p-3 bg-[#FBFBFA]">
              <span className="text-[#94A3B8] font-medium">Budget Envelope</span>
              <p className="mt-1 font-bold text-[#0F172A]">
                {lead.budget_min ? `${formatINR(lead.budget_min)} - ${formatINR(lead.budget_max || lead.budget_min)}` : "Not quoted"}
              </p>
            </div>
            <div className="rounded-xl border border-[#F1F5F9] p-3 bg-[#FBFBFA]">
              <span className="text-[#94A3B8] font-medium">Buying Timeline</span>
              <p className="mt-1 font-bold text-[#0F172A]">{lead.buying_timeline || "1-3 months"}</p>
            </div>
          </div>
        </div>

        {/* Multi-Channel Duplicate Attribution History */}
        {lead.duplicate_sources && lead.duplicate_sources.length > 0 && (
          <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50/50 p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-amber-700" />
              <h3 className="text-xs font-bold text-amber-900">Multi-Channel Attribution History</h3>
            </div>
            <p className="mt-1 text-xs text-amber-800">
              This buyer inquired multiple times across distinct marketing campaigns. Historical touches have been preserved:
            </p>
            <div className="mt-2 flex flex-wrap gap-2">
              <span className="rounded-lg bg-white px-2.5 py-1 text-xs font-semibold text-slate-700 border border-amber-200">
                Original Touch: <strong>{lead.source}</strong> ({formatDateTime(lead.created_at)})
              </span>
              {lead.duplicate_sources.map((src, i) => (
                <span key={i} className="rounded-lg bg-white px-2.5 py-1 text-xs font-semibold text-amber-800 border border-amber-200">
                  Subsequent Inquiry: <strong>{src}</strong>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Content Split: Left Conversation Transcript / Right Bookings & Handoff */}
        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Chat History */}
          <div className="lg:col-span-2 rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-sm">
            <div className="flex items-center justify-between border-b border-[#F1F5F9] pb-4">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-emerald-600" />
                <h2 className="text-sm font-bold text-[#0F172A]">Verbatim AI Conversation History</h2>
              </div>
              <span className="text-[11px] text-[#64748B]">Audited & Fact-Sheet Grounded</span>
            </div>

            <div className="mt-4 space-y-4 max-h-[500px] overflow-y-auto pr-2">
              {lead.conversations && lead.conversations.length > 0 && lead.conversations[0].messages.length > 0 ? (
                lead.conversations[0].messages.map((m) => (
                  <div
                    key={m.id}
                    className={`flex flex-col ${m.sender_type === "buyer" ? "items-end" : "items-start"}`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 text-[10px] text-[#94A3B8]">
                      <span>{m.sender_type === "buyer" ? lead.full_name : "EstateFlow AI Assistant"}</span>
                      <span>•</span>
                      <span>{formatDateTime(m.created_at)}</span>
                    </div>
                    <div
                      className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                        m.sender_type === "buyer"
                          ? "bg-[#0F172A] text-white rounded-br-none"
                          : "bg-[#F4F4F2] text-[#0F172A] rounded-bl-none border border-[#EAEAE6]"
                      }`}
                    >
                      {m.content}
                    </div>
                  </div>
                ))
              ) : (
                <div className="py-12 text-center text-xs text-[#94A3B8]">
                  No conversation logs available for this lead.
                </div>
              )}
            </div>
          </div>

          {/* Right: Site Visits & Handoff Dossier */}
          <div className="space-y-6">
            {/* Site Visit Bookings */}
            <div className="rounded-2xl border border-[#EAEAE6] bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 border-b border-[#F1F5F9] pb-3">
                <Calendar className="h-4 w-4 text-emerald-600" />
                <h3 className="text-xs font-bold text-[#0F172A]">Site Visit Bookings</h3>
              </div>

              <div className="mt-3 space-y-3">
                {lead.bookings && lead.bookings.length > 0 ? (
                  lead.bookings.map((b) => (
                    <div key={b.id} className="rounded-xl border border-[#F1F5F9] bg-[#FBFBFA] p-3 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-mono font-bold text-[#0F172A]">{b.booking_reference}</span>
                        <span
                          className={`rounded px-1.5 py-0.5 text-[9px] font-bold ${
                            b.status === "CONFIRMED"
                              ? "bg-emerald-100 text-emerald-800"
                              : b.status === "COMPLETED"
                              ? "bg-teal-100 text-teal-800"
                              : "bg-rose-100 text-rose-800"
                          }`}
                        >
                          {b.status}
                        </span>
                      </div>
                      <p className="mt-1 text-[#475569]">{b.project_name}</p>
                      <p className="text-[11px] font-semibold text-emerald-700 mt-0.5">
                        {formatDateTime(b.slot_start)}
                      </p>
                    </div>
                  ))
                ) : (
                  <div className="py-4 text-center text-xs text-[#94A3B8]">
                    No site visits booked yet.
                  </div>
                )}
              </div>
            </div>

            {/* Sales Handoff Escalation */}
            <div className="rounded-2xl border border-[#EAEAE6] bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 border-b border-[#F1F5F9] pb-3">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <h3 className="text-xs font-bold text-[#0F172A]">Sales Executive Handoff</h3>
              </div>

              <div className="mt-3">
                {lead.handoffs && lead.handoffs.length > 0 ? (
                  lead.handoffs.map((h) => (
                    <div key={h.id} className="rounded-xl border border-amber-200 bg-amber-50/50 p-3 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-900">{h.reason}</span>
                        <span className="rounded bg-amber-200 px-1.5 py-0.5 text-[9px] font-extrabold text-amber-900">
                          {h.priority}
                        </span>
                      </div>
                      <div className="mt-2 text-[11px] text-[#334155] whitespace-pre-line bg-white/70 p-2.5 rounded-lg border border-amber-100 font-sans">
                        {h.structured_summary}
                      </div>
                      {h.recommended_action && (
                        <div className="mt-2 text-[11px] font-semibold text-emerald-800">
                          Next Action: {h.recommended_action}
                        </div>
                      )}
                    </div>
                  ))
                ) : (
                  <div className="py-4 text-center text-xs text-[#94A3B8]">
                    No active escalations. Handled normally by conversational AI.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
