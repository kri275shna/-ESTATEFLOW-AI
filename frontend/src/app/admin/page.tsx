'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';

interface PropertyFact {
  id: string;
  project_id: string;
  project_name: string;
  category: string;
  attribute_name: string;
  approved_fact: string;
  is_public: boolean;
  updated_at: string;
  updated_by?: string;
}

interface VisitSlotItem {
  id: string;
  project_id: string;
  project_name: string;
  slot_start: string;
  slot_end: string;
  max_capacity: number;
  booked_count: number;
  available_spots: number;
  is_blocked: boolean;
}

interface AuditLogItem {
  id: string;
  user_name: string;
  action: string;
  entity_type: string;
  entity_id: string;
  change_summary: string;
  created_at: string;
}

export default function AdminConfigPage() {
  const [activeTab, setActiveTab] = useState<'facts' | 'slots' | 'audit'>('facts');
  const [facts, setFacts] = useState<PropertyFact[]>([]);
  const [slots, setSlots] = useState<VisitSlotItem[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Form states for new fact
  const [showAddFactModal, setShowAddFactModal] = useState(false);
  const [editingFact, setEditingFact] = useState<PropertyFact | null>(null);
  const [newProjectId, setNewProjectId] = useState<string>('');
  const [newCategory, setNewCategory] = useState<string>('Configuration');
  const [newAttribute, setNewAttribute] = useState<string>('');
  const [newFactValue, setNewFactValue] = useState<string>('');

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        setError('Please sign in as Admin or Sales Head to manage configurations.');
        setLoading(false);
        return;
      }

      const headers = { Authorization: `Bearer ${token}` };

      // Load facts
      const factsRes = await fetch('http://localhost:8000/api/v1/admin/facts', { headers });
      if (factsRes.ok) {
        const factsJson = await factsRes.json();
        setFacts(factsJson);
        if (factsJson.length > 0 && !newProjectId) {
          setNewProjectId(factsJson[0].project_id);
        }
      }

      // Load slots
      const slotsRes = await fetch('http://localhost:8000/api/v1/admin/slots', { headers });
      if (slotsRes.ok) {
        setSlots(await slotsRes.json());
      }

      // Load audit logs
      const auditRes = await fetch('http://localhost:8000/api/v1/admin/audit-logs', { headers });
      if (auditRes.ok) {
        setAuditLogs(await auditRes.json());
      }
    } catch (err: any) {
      setError(err.message || 'Error communicating with configuration service.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateFact = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('http://localhost:8000/api/v1/admin/facts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          project_id: newProjectId,
          category: newCategory,
          attribute_name: newAttribute,
          approved_fact: newFactValue,
          is_public: true
        })
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Failed to save fact');
      }

      setActionSuccess('Approved fact published to AI assistant grounding engine!');
      setShowAddFactModal(false);
      setNewAttribute('');
      setNewFactValue('');
      setTimeout(() => setActionSuccess(null), 3000);
      fetchData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleUpdateFact = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingFact) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/api/v1/admin/facts/${editingFact.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          category: editingFact.category,
          attribute_name: editingFact.attribute_name,
          approved_fact: editingFact.approved_fact,
          is_public: editingFact.is_public
        })
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Failed to update fact');
      }

      setActionSuccess('Approved fact updated and logged to audit trail.');
      setEditingFact(null);
      setTimeout(() => setActionSuccess(null), 3000);
      fetchData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleDeleteFact = async (factId: string) => {
    if (!confirm('Are you sure you want to remove this fact from the AI grounding sheet?')) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/api/v1/admin/facts/${factId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Failed to delete fact');
      }

      setActionSuccess('Fact deleted and recorded in audit log.');
      setTimeout(() => setActionSuccess(null), 3000);
      fetchData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleUpdateSlotCapacity = async (slotId: string, currentCap: number, delta: number) => {
    const newCap = currentCap + delta;
    if (newCap < 1) return;

    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`http://localhost:8000/api/v1/admin/slots/${slotId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          max_capacity: newCap
        })
      });

      if (!res.ok) {
        const errJson = await res.json();
        throw new Error(errJson.detail || 'Failed to update slot');
      }

      setActionSuccess(`Slot capacity updated to ${newCap}`);
      setTimeout(() => setActionSuccess(null), 3000);
      fetchData();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const formatSlotTime = (isoString: string) => {
    try {
      const d = new Date(isoString);
      return `${d.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })} at ${d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}`;
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
              <h1 className="text-3xl font-bold tracking-tight text-white">Admin Configuration</h1>
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20">
                Governance &amp; Controls
              </span>
            </div>
            <p className="text-sm text-slate-400 mt-1">
              Manage approved AI fact sheets, visit slot capacities, and inspect security audit logs.
            </p>
          </div>

          <div className="flex items-center gap-3">
            {activeTab === 'facts' && (
              <button
                onClick={() => setShowAddFactModal(true)}
                className="px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm"
              >
                + Add Approved Fact
              </button>
            )}
            <Link
              href="/analytics"
              className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
            >
              Analytics Dashboard →
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
              Sign In as Admin
            </Link>
          </div>
        )}

        {/* Tab Controls */}
        <div className="flex border-b border-slate-800 gap-6 text-sm font-semibold">
          <button
            onClick={() => setActiveTab('facts')}
            className={`pb-3 border-b-2 transition ${
              activeTab === 'facts'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            📋 Property Fact Sheet ({facts.length})
          </button>
          <button
            onClick={() => setActiveTab('slots')}
            className={`pb-3 border-b-2 transition ${
              activeTab === 'slots'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🗓️ Slot Capacity &amp; Limits ({slots.length})
          </button>
          <button
            onClick={() => setActiveTab('audit')}
            className={`pb-3 border-b-2 transition ${
              activeTab === 'audit'
                ? 'border-emerald-500 text-emerald-400'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            🛡️ Audit Logs ({auditLogs.length})
          </button>
        </div>

        {loading && (
          <div className="py-24 text-center text-slate-500">
            <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            Loading configuration data...
          </div>
        )}

        {/* TAB 1: FACT SHEET */}
        {!loading && activeTab === 'facts' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
              <span className="text-base">ℹ️</span>
              <span>
                <strong>AI Grounding Rule:</strong> The conversational assistant strictly answers property questions using these approved database facts. Missing facts trigger escalation to human sales executives.
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {facts.map((f) => (
                <div
                  key={f.id}
                  className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold px-2.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                        {f.category}
                      </span>
                      <span className="text-xs text-slate-400 font-medium">{f.project_name}</span>
                    </div>

                    <h3 className="text-base font-bold text-white">{f.attribute_name}</h3>
                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-3 rounded-xl border border-slate-900">
                      {f.approved_fact}
                    </p>
                  </div>

                  <div className="pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs">
                    <span className="text-slate-500 font-mono text-[11px]">
                      Updated: {new Date(f.updated_at).toLocaleDateString('en-IN')}
                    </span>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setEditingFact(f)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition font-medium"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => handleDeleteFact(f.id)}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-rose-950/60 text-slate-400 hover:text-rose-300 transition font-medium"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: VISIT SLOTS CAPACITY */}
        {!loading && activeTab === 'slots' && (
          <div className="space-y-4">
            <div className="p-4 rounded-xl bg-slate-900/40 border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
              <span className="text-base">ℹ️</span>
              <span>
                <strong>Concurrency Engine:</strong> Database row-level locks prevent over-booking. You can adjust the maximum concurrent appointments allowed per slot here.
              </span>
            </div>

            <div className="overflow-x-auto rounded-2xl border border-slate-800">
              <table className="w-full text-left text-sm text-slate-300 bg-slate-900/60">
                <thead className="bg-slate-950 text-slate-400 text-xs uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Slot Window</th>
                    <th className="py-3 px-4 font-semibold">Project</th>
                    <th className="py-3 px-4 font-semibold">Booked</th>
                    <th className="py-3 px-4 font-semibold">Max Capacity</th>
                    <th className="py-3 px-4 font-semibold">Available</th>
                    <th className="py-3 px-4 font-semibold">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
                  {slots.slice(0, 30).map((s) => (
                    <tr key={s.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-sans font-medium text-white">{formatSlotTime(s.slot_start)}</td>
                      <td className="py-3 px-4 font-sans text-slate-300">{s.project_name}</td>
                      <td className="py-3 px-4 text-blue-400 font-bold">{s.booked_count}</td>
                      <td className="py-3 px-4 font-bold text-white">{s.max_capacity}</td>
                      <td className="py-3 px-4 text-emerald-400 font-bold">{s.available_spots}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5 font-sans">
                          <button
                            onClick={() => handleUpdateSlotCapacity(s.id, s.max_capacity, 1)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition font-bold"
                            title="Increase capacity"
                          >
                            +1
                          </button>
                          <button
                            disabled={s.max_capacity <= s.booked_count}
                            onClick={() => handleUpdateSlotCapacity(s.id, s.max_capacity, -1)}
                            className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition font-bold disabled:opacity-40"
                            title="Decrease capacity"
                          >
                            -1
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 3: AUDIT LOGS */}
        {!loading && activeTab === 'audit' && (
          <div className="space-y-4">
            <div className="overflow-x-auto rounded-2xl border border-slate-800">
              <table className="w-full text-left text-sm text-slate-300 bg-slate-900/60">
                <thead className="bg-slate-950 text-slate-400 text-xs uppercase border-b border-slate-800">
                  <tr>
                    <th className="py-3 px-4 font-semibold">Timestamp</th>
                    <th className="py-3 px-4 font-semibold">User</th>
                    <th className="py-3 px-4 font-semibold">Action</th>
                    <th className="py-3 px-4 font-semibold">Entity</th>
                    <th className="py-3 px-4 font-semibold">Change Summary</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-xs">
                  {auditLogs.map((a) => (
                    <tr key={a.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap">
                        {new Date(a.created_at).toLocaleString('en-IN')}
                      </td>
                      <td className="py-3 px-4 font-bold text-white">{a.user_name}</td>
                      <td className="py-3 px-4">
                        <span className="font-mono px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 text-[11px]">
                          {a.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">{a.entity_type}</td>
                      <td className="py-3 px-4 text-slate-300 font-mono text-[11px] max-w-md truncate">
                        {a.change_summary}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* MODAL: Add Fact */}
        {showAddFactModal && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="text-lg font-bold text-white">+ Add Approved Property Fact</h3>
                <button onClick={() => setShowAddFactModal(false)} className="text-slate-400 hover:text-white">✕</button>
              </div>

              <form onSubmit={handleCreateFact} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Target Project</label>
                  <select
                    value={newProjectId}
                    onChange={(e) => setNewProjectId(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                  >
                    {Array.from(new Set(facts.map(f => f.project_id))).map(pid => {
                      const f = facts.find(x => x.project_id === pid);
                      return <option key={pid} value={pid}>{f?.project_name || pid}</option>;
                    })}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                  >
                    <option value="Pricing">Pricing</option>
                    <option value="Configuration">Configuration</option>
                    <option value="Amenities">Amenities</option>
                    <option value="Location">Location</option>
                    <option value="RERA">RERA</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Attribute Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Swimming Pool & Gym Facilities"
                    value={newAttribute}
                    onChange={(e) => setNewAttribute(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Approved Fact Content</label>
                  <textarea
                    required
                    rows={4}
                    placeholder="Enter factual description that the AI assistant can quote directly..."
                    value={newFactValue}
                    onChange={(e) => setNewFactValue(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowAddFactModal(false)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition"
                  >
                    Publish Fact
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* MODAL: Edit Fact */}
        {editingFact && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 space-y-4 shadow-2xl">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <h3 className="text-lg font-bold text-white">Edit Approved Property Fact</h3>
                <button onClick={() => setEditingFact(null)} className="text-slate-400 hover:text-white">✕</button>
              </div>

              <form onSubmit={handleUpdateFact} className="space-y-4 text-sm">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Category</label>
                  <input
                    type="text"
                    value={editingFact.category}
                    onChange={(e) => setEditingFact({ ...editingFact, category: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Attribute Name</label>
                  <input
                    type="text"
                    value={editingFact.attribute_name}
                    onChange={(e) => setEditingFact({ ...editingFact, attribute_name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Approved Fact Content</label>
                  <textarea
                    rows={4}
                    value={editingFact.approved_fact}
                    onChange={(e) => setEditingFact({ ...editingFact, approved_fact: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-white"
                  />
                </div>

                <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setEditingFact(null)}
                    className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition"
                  >
                    Save &amp; Log Changes
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
