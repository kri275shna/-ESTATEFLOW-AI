'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';

interface AnalyticsData {
  summary: {
    total_leads: number;
    new_leads: number;
    qualified_leads: number;
    total_bookings: number;
    confirmed_visits: number;
    completed_visits: number;
    no_show_visits: number;
    cancelled_visits: number;
    show_up_rate: number;
    lead_to_visit_rate: number;
    avg_first_response_minutes: number;
    median_first_response_minutes: number;
    uncontacted_48h: number;
    uncontacted_48h_pct: number;
    monthly_marketing_spend: number;
    cost_per_lead: number;
    cost_per_completed_visit: number;
  };
  target_comparison: {
    first_response: { before: string; target: string; achieved: string; status: string };
    uncontacted_48h: { before: string; target: string; achieved: string; status: string };
    conversion_to_visit: { before: string; target: string; achieved: string; status: string };
  };
  funnel: Array<{ stage: string; count: number; conversion_pct: number }>;
  source_distribution: Array<{
    source: string;
    leads: number;
    share_pct: number;
    visits_booked: number;
    visits_completed: number;
    spend: number;
    cost_per_lead: number | null;
  }>;
  project_distribution: Array<{
    project_id: string;
    project_name: string;
    location: string;
    total_apartments: number;
    leads: number;
    visits_booked: number;
    visits_completed: number;
  }>;
  exec_leaderboard: Array<{
    id: string;
    name: string;
    phone: string;
    assigned_leads: number;
    total_visits: number;
    completed_visits: number;
    show_up_rate: number;
  }>;
}

export default function AnalyticsDashboardPage() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Please sign in as Sales Head or Admin to view executive analytics.');
        setLoading(false);
        return;
      }

      const res = await fetch('http://localhost:8000/api/v1/analytics/overview', {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });

      if (!res.ok) {
        if (res.status === 403) {
          throw new Error('Access restricted: Only Sales Head and Admin can view analytics.');
        }
        throw new Error('Failed to load analytics.');
      }

      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || 'Error fetching analytics data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Navbar />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight text-white">Executive Business Analytics</h1>
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Live DB Aggregation
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Real-time pipeline metrics, conversion funnel, response SLA tracking, and marketing ROI.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchAnalytics}
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              ↻ Refresh Metrics
            </button>
            <Link
              href="/admin"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              Admin Config →
            </Link>
          </div>
        </div>

        {error && (
          <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-500/30 text-rose-300 space-y-3">
            <p className="font-semibold">{error}</p>
            <Link
              href="/login"
              className="inline-block px-4 py-2 rounded-lg bg-rose-600 text-white text-sm hover:bg-rose-500 transition"
            >
              Sign In as Sales Head / Admin
            </Link>
          </div>
        )}

        {loading && !data && (
          <div className="py-24 text-center text-slate-500">
            <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            Aggregating database KPIs and spend metrics...
          </div>
        )}

        {data && (
          <div className="space-y-8">
            {/* Target vs Achieved Banner */}
            <div className="p-6 rounded-2xl bg-slate-900/90 border border-emerald-500/30 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-base font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <span>🎯</span> Client Target SLA Scorecard
                </h2>
                <span className="text-xs text-slate-400">Baseline vs AI-Assisted Performance</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Median First Response</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400">
                      {data.target_comparison.first_response.status}
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-emerald-400">
                    {data.target_comparison.first_response.achieved}
                  </p>
                  <div className="text-xs text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/80">
                    <span>Target: {data.target_comparison.first_response.target}</span>
                    <span className="text-rose-400/80 line-through">Prior: {data.target_comparison.first_response.before}</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Uncontacted &gt;48 Hours</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400">
                      {data.target_comparison.uncontacted_48h.status}
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-emerald-400">
                    {data.target_comparison.uncontacted_48h.achieved}
                  </p>
                  <div className="text-xs text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/80">
                    <span>Target: {data.target_comparison.uncontacted_48h.target}</span>
                    <span className="text-rose-400/80 line-through">Prior: {data.target_comparison.uncontacted_48h.before}</span>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-slate-400 uppercase font-semibold">Lead-to-Visit Rate</span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-emerald-500/20 text-emerald-400">
                      {data.target_comparison.conversion_to_visit.status}
                    </span>
                  </div>
                  <p className="text-2xl font-bold text-emerald-400">
                    {data.target_comparison.conversion_to_visit.achieved}
                  </p>
                  <div className="text-xs text-slate-400 flex items-center justify-between pt-1 border-t border-slate-800/80">
                    <span>Target: {data.target_comparison.conversion_to_visit.target}</span>
                    <span className="text-rose-400/80 line-through">Prior: {data.target_comparison.conversion_to_visit.before}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Core Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Leads</p>
                <p className="text-2xl font-bold text-white mt-1">{data.summary.total_leads}</p>
                <p className="text-xs text-slate-400 mt-2">{data.summary.new_leads} awaiting action</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Qualified Leads</p>
                <p className="text-2xl font-bold text-emerald-400 mt-1">{data.summary.qualified_leads}</p>
                <p className="text-xs text-emerald-400/80 mt-2">
                  {Math.round((data.summary.qualified_leads / data.summary.total_leads) * 100)}% of total
                </p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Visits Booked</p>
                <p className="text-2xl font-bold text-blue-400 mt-1">{data.summary.total_bookings}</p>
                <p className="text-xs text-blue-300/80 mt-2">{data.summary.confirmed_visits} upcoming</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Show-Up Rate</p>
                <p className="text-2xl font-bold text-cyan-400 mt-1">{data.summary.show_up_rate}%</p>
                <p className="text-xs text-slate-400 mt-2">{data.summary.completed_visits} completed</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Cost Per Lead</p>
                <p className="text-2xl font-bold text-amber-400 mt-1">{formatCurrency(data.summary.cost_per_lead)}</p>
                <p className="text-xs text-slate-400 mt-2">Total: {formatCurrency(data.summary.monthly_marketing_spend)}</p>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800/80">
                <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">Cost / Completed Visit</p>
                <p className="text-2xl font-bold text-purple-400 mt-1">{formatCurrency(data.summary.cost_per_completed_visit)}</p>
                <p className="text-xs text-slate-400 mt-2">Unit conversion cost</p>
              </div>
            </div>

            {/* Funnel & Source Breakdown Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Funnel */}
              <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white">Conversion Funnel</h3>
                  <p className="text-xs text-slate-400">Buyer journey from initial ad click to physical site visit</p>
                </div>

                <div className="space-y-4">
                  {data.funnel.map((f, i) => (
                    <div key={f.stage} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs font-medium">
                        <span className="text-slate-300 flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center text-[10px] font-bold">
                            {i + 1}
                          </span>
                          {f.stage}
                        </span>
                        <div className="flex items-center gap-3">
                          <span className="font-bold text-white">{f.count}</span>
                          <span className="text-emerald-400 font-mono text-[11px] w-12 text-right">
                            {f.conversion_pct}%
                          </span>
                        </div>
                      </div>
                      <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-slate-800">
                        <div
                          className="bg-gradient-to-r from-emerald-600 to-teal-400 h-2.5 rounded-full transition-all duration-500"
                          style={{ width: `${Math.max(f.conversion_pct, 4)}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Project Performance */}
              <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-6">
                <div>
                  <h3 className="text-lg font-bold text-white">Project Performance</h3>
                  <p className="text-xs text-slate-400">Demand distribution across active residential developments</p>
                </div>

                <div className="space-y-4">
                  {data.project_distribution.map((proj) => (
                    <div key={proj.project_id} className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-bold text-white text-base">{proj.project_name}</p>
                          <p className="text-xs text-slate-400">{proj.location} • {proj.total_apartments} Apartments</p>
                        </div>
                        <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-mono">
                          {proj.leads} Leads
                        </span>
                      </div>

                      <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-900 text-xs">
                        <div>
                          <span className="text-slate-400">Visits Booked:</span>{' '}
                          <span className="font-bold text-white">{proj.visits_booked}</span>
                        </div>
                        <div>
                          <span className="text-slate-400">Completed Tours:</span>{' '}
                          <span className="font-bold text-emerald-400">{proj.visits_completed}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Source Attribution Table */}
            <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">Source Attribution &amp; Spend Efficiency</h3>
                  <p className="text-xs text-slate-400">ROI by acquisition channel based on ₹30L monthly marketing spend</p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 text-xs uppercase border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Channel</th>
                      <th className="py-3 px-4 font-semibold">Leads</th>
                      <th className="py-3 px-4 font-semibold">Share</th>
                      <th className="py-3 px-4 font-semibold">Visits Booked</th>
                      <th className="py-3 px-4 font-semibold">Visits Completed</th>
                      <th className="py-3 px-4 font-semibold">Spend</th>
                      <th className="py-3 px-4 font-semibold">Cost / Lead</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                    {data.source_distribution.map((s) => (
                      <tr key={s.source} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-4 font-sans font-bold text-white">{s.source}</td>
                        <td className="py-3 px-4">{s.leads}</td>
                        <td className="py-3 px-4 text-slate-400">{s.share_pct}%</td>
                        <td className="py-3 px-4 text-blue-400">{s.visits_booked}</td>
                        <td className="py-3 px-4 text-emerald-400 font-bold">{s.visits_completed}</td>
                        <td className="py-3 px-4 text-slate-300">{s.spend > 0 ? formatCurrency(s.spend) : '—'}</td>
                        <td className="py-3 px-4 text-amber-400 font-semibold">{s.cost_per_lead ? formatCurrency(s.cost_per_lead) : '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Sales Executive Leaderboard */}
            <div className="p-6 rounded-2xl bg-slate-900/70 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-lg font-bold text-white">Sales Team Performance Leaderboard</h3>
                  <p className="text-xs text-slate-400">11 sales executives ranked by completed site visits and buyer show-up rates</p>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 text-xs uppercase border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4 font-semibold">Rank</th>
                      <th className="py-3 px-4 font-semibold">Sales Representative</th>
                      <th className="py-3 px-4 font-semibold">Assigned Leads</th>
                      <th className="py-3 px-4 font-semibold">Total Visits</th>
                      <th className="py-3 px-4 font-semibold">Completed Tours</th>
                      <th className="py-3 px-4 font-semibold">Show-Up Rate</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 text-xs">
                    {data.exec_leaderboard.map((rep, index) => (
                      <tr key={rep.id} className="hover:bg-slate-800/40 transition">
                        <td className="py-3 px-4 font-mono font-bold text-slate-400">
                          {index === 0 ? '🥇 1' : index === 1 ? '🥈 2' : index === 2 ? '🥉 3' : `#${index + 1}`}
                        </td>
                        <td className="py-3 px-4">
                          <p className="font-bold text-white">{rep.name}</p>
                          <p className="text-slate-500 font-mono text-[11px]">{rep.phone}</p>
                        </td>
                        <td className="py-3 px-4 font-mono">{rep.assigned_leads}</td>
                        <td className="py-3 px-4 font-mono text-blue-400">{rep.total_visits}</td>
                        <td className="py-3 px-4 font-mono text-emerald-400 font-bold">{rep.completed_visits}</td>
                        <td className="py-3 px-4 font-mono">
                          <span className={`px-2 py-0.5 rounded ${
                            rep.show_up_rate >= 70 ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-800 text-slate-400'
                          }`}>
                            {rep.show_up_rate}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
