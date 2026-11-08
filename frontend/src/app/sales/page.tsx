'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';

interface WorkspaceData {
  user_name: string;
  user_role: string;
  kpis: {
    total_assigned_leads: number;
    new_leads: number;
    qualified_leads: number;
    needs_followup: number;
    uncontacted_48h: number;
    today_visits_count: number;
    pending_handoffs_count: number;
  };
  todays_visits: Array<{
    booking_id: string;
    booking_reference: string;
    status: string;
    lead_name: string;
    lead_phone: string;
    lead_reference: string;
    project_name: string;
    slot_start: string;
    slot_end: string;
    notes?: string;
  }>;
  upcoming_visits: Array<{
    booking_id: string;
    booking_reference: string;
    status: string;
    lead_name: string;
    lead_phone: string;
    project_name: string;
    slot_start: string;
    slot_end: string;
  }>;
  pending_handoffs: Array<{
    id: string;
    lead_id: string;
    lead_name: string;
    lead_phone: string;
    lead_reference: string;
    conversation_id?: string;
    reason: string;
    priority: string;
    structured_summary: string;
    recommended_action?: string;
    created_at: string;
  }>;
}

export default function SalesWorkspacePage() {
  const [data, setData] = useState<WorkspaceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [updatingHandoffId, setUpdatingHandoffId] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [selectedHandoff, setSelectedHandoff] = useState<any | null>(null);

  const fetchWorkspace = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Please sign in as Sales Executive, Sales Head, or Admin.');
        setLoading(false);
        return;
      }

      const res = await fetch('http://localhost:8000/api/v1/handoffs/workspace/overview', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Access restricted to Sales Executives, Sales Heads, and Administrators.');
        }
        throw new Error('Failed to load sales workspace data.');
      }

      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Error connecting to workspace service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspace();
  }, []);

  const handleUpdateBookingStatus = async (bookingId: string, newStatus: string) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/api/v1/bookings/${bookingId}/status?status=${newStatus}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      if (res.ok) {
        setActionSuccess(`Visit status updated to ${newStatus}`);
        setTimeout(() => setActionSuccess(null), 3000);
        fetchWorkspace();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleResolveHandoff = async (handoffId: string) => {
    setUpdatingHandoffId(handoffId);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/api/v1/handoffs/${handoffId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          status: 'RESOLVED',
          notes: 'Customer contacted via direct outreach.'
        })
      });
      if (res.ok) {
        setActionSuccess('Handoff marked as RESOLVED and buyer status updated.');
        setTimeout(() => setActionSuccess(null), 3000);
        setSelectedHandoff(null);
        fetchWorkspace();
      }
    } catch (e) {
      console.error(e);
    } finally {
      setUpdatingHandoffId(null);
    }
  };

  const formatSlotTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true });
    } catch {
      return isoString;
    }
  };

  const formatSlotDate = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric', weekday: 'short' });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-white">Sales Executive Workspace</h1>
              {data && (
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  {data.user_role}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Active assigned leads, today&apos;s site visits, and escalated AI conversations.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/leads"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              All Leads Pipeline →
            </Link>
            <Link
              href="/book"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm"
            >
              Book New Visit
            </Link>
          </div>
        </div>

        {actionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-sm flex items-center justify-between">
            <span>✓ {actionSuccess}</span>
            <button onClick={() => setActionSuccess(null)} className="text-emerald-400 hover:text-white">✕</button>
          </div>
        )}

        {error && (
          <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-300 space-y-3">
            <p className="font-semibold">{error}</p>
            <Link
              href="/login"
              className="inline-block px-4 py-2 rounded-lg bg-rose-600 text-white text-sm hover:bg-rose-500 transition"
            >
              Sign In to Continue
            </Link>
          </div>
        )}

        {loading && !data && (
          <div className="py-24 text-center text-slate-500">
            <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            Loading your sales workspace...
          </div>
        )}

        {data && (
          <div className="space-y-8">
            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Assigned Leads</p>
                <p className="text-2xl font-bold text-white mt-1">{data.kpis.total_assigned_leads}</p>
                <div className="flex gap-2 text-xs mt-2 text-slate-400">
                  <span className="text-emerald-400 font-semibold">{data.kpis.qualified_leads} qualified</span>
                  <span>•</span>
                  <span className="text-cyan-400">{data.kpis.new_leads} new</span>
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Visits Today</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{data.kpis.today_visits_count}</p>
                <p className="text-xs text-slate-400 mt-2">Scheduled on site</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Pending Handoffs</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">{data.kpis.pending_handoffs_count}</p>
                <p className="text-xs text-amber-300/80 mt-2">Awaiting your call</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Human Follow-up</p>
                <p className="text-2xl font-bold text-rose-400 mt-1">{data.kpis.needs_followup}</p>
                <p className="text-xs text-slate-400 mt-2">Escalated buyers</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80 col-span-2 sm:col-span-1">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Uncontacted &gt;48h</p>
                <p className="text-2xl font-bold text-white mt-1">{data.kpis.uncontacted_48h}</p>
                <p className="text-xs text-rose-400 mt-2">Target &lt; 5% SLA</p>
              </div>
            </div>

            {/* Today's Visits Grid */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>📅</span> Today&apos;s Site Visits
                  </h2>
                  <p className="text-xs text-slate-400">Buyers scheduled to tour the properties today</p>
                </div>
                <span className="text-xs text-slate-500 font-mono">
                  {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
                </span>
              </div>

              {data.todays_visits.length === 0 ? (
                <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800/60 text-center text-slate-400">
                  <p className="text-base font-medium">No site visits scheduled for today yet.</p>
                  <p className="text-xs text-slate-500 mt-1">Upcoming visits scheduled later this week are shown below.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {data.todays_visits.map((v) => (
                    <div
                      key={v.booking_id}
                      className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-4"
                    >
                      <div className="space-y-2">
                        <div className="flex items-start justify-between">
                          <span className="text-xs font-mono font-semibold px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            {formatSlotTime(v.slot_start)} - {formatSlotTime(v.slot_end)}
                          </span>
                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                              v.status === 'CONFIRMED'
                                ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                                : v.status === 'COMPLETED'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                                : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                            }`}
                          >
                            {v.status}
                          </span>
                        </div>

                        <div>
                          <p className="text-lg font-bold text-white">{v.lead_name}</p>
                          <p className="text-xs font-mono text-slate-400">{v.lead_phone}</p>
                        </div>

                        <div className="text-xs text-slate-300">
                          <p className="font-semibold text-slate-200">{v.project_name}</p>
                          <p className="text-slate-500 font-mono text-[11px] mt-0.5">Ref: {v.booking_reference}</p>
                        </div>
                      </div>

                      {/* Status Action Buttons */}
                      <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between gap-2">
                        {v.status === 'CONFIRMED' ? (
                          <>
                            <button
                              onClick={() => handleUpdateBookingStatus(v.booking_id, 'COMPLETED')}
                              className="flex-1 py-1.5 px-3 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition text-center"
                            >
                              ✓ Attended
                            </button>
                            <button
                              onClick={() => handleUpdateBookingStatus(v.booking_id, 'NO_SHOW')}
                              className="py-1.5 px-3 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-rose-900/60 text-slate-300 hover:text-rose-200 transition"
                            >
                              No-Show
                            </button>
                          </>
                        ) : (
                          <span className="text-xs text-slate-500 italic">Attendance marked as {v.status}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Pending Flagged AI Handoffs */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>⚡</span> Flagged Conversations &amp; Escalations
                  </h2>
                  <p className="text-xs text-slate-400">Buyers requesting sales calls or requiring compliance review</p>
                </div>
                <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
                  {data.pending_handoffs.length} Action Needed
                </span>
              </div>

              {data.pending_handoffs.length === 0 ? (
                <div className="p-8 rounded-2xl bg-slate-900/40 border border-slate-800/60 text-center text-slate-400">
                  <p className="text-base font-medium">All flagged conversations have been addressed!</p>
                  <p className="text-xs text-slate-500 mt-1">New escalations from the AI assistant will appear here in real-time.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {data.pending_handoffs.map((h) => (
                    <div
                      key={h.id}
                      className="p-5 rounded-2xl bg-slate-900/80 border border-amber-500/20 hover:border-amber-500/40 transition space-y-4"
                    >
                      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <span className={`px-2.5 py-0.5 rounded text-xs font-bold ${
                            h.priority === 'URGENT' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
                          }`}>
                            {h.priority}
                          </span>
                          <div>
                            <span className="text-base font-bold text-white">{h.lead_name}</span>
                            <span className="text-xs font-mono text-slate-400 ml-2">{h.lead_phone}</span>
                            <span className="text-xs text-slate-500 font-mono ml-2">({h.lead_reference})</span>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <button
                            onClick={() => setSelectedHandoff(selectedHandoff?.id === h.id ? null : h)}
                            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition font-medium"
                          >
                            {selectedHandoff?.id === h.id ? 'Hide Dossier' : 'View AI Summary'}
                          </button>
                          <Link
                            href={`/leads/${h.lead_id}`}
                            className="text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 transition font-medium"
                          >
                            Lead Details →
                          </Link>
                          <button
                            disabled={updatingHandoffId === h.id}
                            onClick={() => handleResolveHandoff(h.id)}
                            className="text-xs px-3.5 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition disabled:opacity-50"
                          >
                            {updatingHandoffId === h.id ? 'Updating...' : 'Mark Contacted'}
                          </button>
                        </div>
                      </div>

                      <div className="text-xs text-slate-300">
                        <span className="font-semibold text-amber-300">Reason:</span> {h.reason}
                        {h.recommended_action && (
                          <div className="mt-1 text-slate-400">
                            <span className="font-semibold text-slate-300">Next Action:</span> {h.recommended_action}
                          </div>
                        )}
                      </div>

                      {/* Expandable Dossier */}
                      {selectedHandoff?.id === h.id && (
                        <div className="mt-3 p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
                          <p className="text-amber-400 font-bold mb-2">📋 AI QUALIFICATION DOSSIER</p>
                          {h.structured_summary}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </section>

            {/* Upcoming Visits */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-xl font-bold text-white flex items-center gap-2">
                    <span>🗓️</span> Upcoming Visits (Next 7 Days)
                  </h2>
                  <p className="text-xs text-slate-400">Future scheduled property visits</p>
                </div>
                <span className="text-xs font-semibold text-slate-400">{data.upcoming_visits.length} booked</span>
              </div>

              {data.upcoming_visits.length === 0 ? (
                <div className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/60 text-center text-slate-400">
                  <p className="text-xs">No upcoming site visits in the next 7 days.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {data.upcoming_visits.map((u) => (
                    <div key={u.booking_id} className="p-4 rounded-xl bg-slate-900/50 border border-slate-800 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-semibold text-white">{u.lead_name}</p>
                        <p className="text-xs text-slate-400">{u.project_name}</p>
                        <p className="text-[11px] font-mono text-slate-500 mt-1">
                          {formatSlotDate(u.slot_start)} at {formatSlotTime(u.slot_start)}
                        </p>
                      </div>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20">
                        {u.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}
      </main>
    </div>
  );
}
