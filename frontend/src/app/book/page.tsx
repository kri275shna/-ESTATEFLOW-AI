"use client";

import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import { formatDateTime } from "@/lib/utils";
import { 
  Calendar as CalendarIcon, Clock, MapPin, ShieldCheck, 
  CheckCircle2, AlertCircle, Loader2, User, Phone, 
  Building2, ArrowRight, Bell, Sparkles
} from "lucide-react";
import { getStoredUser } from "@/lib/auth";

interface VisitSlot {
  id: string;
  project_id: string;
  project_name: string;
  slot_start: string;
  slot_end: string;
  max_capacity: number;
  booked_count: number;
  available_spots: number;
  is_available: boolean;
}

interface ConfirmedBooking {
  booking_reference: string;
  project_name: string;
  location: string;
  rera_number: string;
  slot_start: string;
  assigned_salesperson_name: string;
  assigned_salesperson_phone: string;
  buyer_name: string;
  buyer_phone: string;
}

export default function BookingPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [slots, setSlots] = useState<VisitSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(true);
  const [selectedSlotId, setSelectedSlotId] = useState<string | null>(null);

  // Form Fields
  const [buyerName, setBuyerName] = useState("Gaurav Mehta");
  const [rawPhone, setRawPhone] = useState("+91 98250 00099");
  const [email, setEmail] = useState("gaurav.mehta@gmail.com");
  const [preferredBhk, setPreferredBhk] = useState("3 BHK");
  const [notes, setNotes] = useState("Interested in higher floor unit with garden view");

  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingError, setBookingError] = useState<string | null>(null);
  const [confirmedBooking, setConfirmedBooking] = useState<ConfirmedBooking | null>(null);

  // Load projects
  useEffect(() => {
    const user = getStoredUser();
    if (user) {
      setBuyerName(user.full_name);
      if (user.phone) setRawPhone(user.phone);
      if (user.email) setEmail(user.email);
    }

    const fetchProjects = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/v1/health");
        // We will fetch slots for both projects
        fetchSlots();
      } catch {}
    };
    fetchProjects();
  }, []);

  const fetchSlots = async (pId?: string) => {
    setLoadingSlots(true);
    try {
      const url = pId && pId !== "ALL"
        ? `http://localhost:8000/api/v1/bookings/slots?project_id=${pId}&days_ahead=10`
        : `http://localhost:8000/api/v1/bookings/slots?days_ahead=10`;
      
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setSlots(data);

        // Extract distinct projects
        const projs = Array.from(
          new Map(data.map((s: VisitSlot) => [s.project_id, { id: s.project_id, name: s.project_name }])).values()
        );
        setProjects(projs);
        if (!selectedProjectId && projs.length > 0) {
          setSelectedProjectId((projs[0] as any).id);
        }
      }
    } catch (err) {
      console.error("Failed to load slots", err);
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleProjectSelect = (pId: string) => {
    setSelectedProjectId(pId);
    setSelectedSlotId(null);
  };

  const filteredSlots = selectedProjectId
    ? slots.filter((s) => s.project_id === selectedProjectId)
    : slots;

  // Group slots by Date string
  const groupedSlots = filteredSlots.reduce((acc: Record<string, VisitSlot[]>, slot) => {
    const d = new Date(slot.slot_start);
    const dateKey = d.toLocaleDateString("en-IN", {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
    if (!acc[dateKey]) acc[dateKey] = [];
    acc[dateKey].push(slot);
    return acc;
  }, {});

  const handleBookingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSlotId) {
      setBookingError("Please select an available visit slot from the grid below.");
      return;
    }

    setBookingError(null);
    setBookingLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/v1/bookings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          slot_id: selectedSlotId,
          project_id: selectedProjectId,
          buyer_name: buyerName,
          raw_phone: rawPhone,
          email: email,
          preferred_bhk: preferredBhk,
          notes: notes,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Booking failed (${res.status})`);
      }

      const data = await res.json();
      setConfirmedBooking(data);
      fetchSlots(selectedProjectId);
    } catch (err: any) {
      setBookingError(err.message || "Failed to confirm visit slot.");
    } finally {
      setBookingLoading(false);
    }
  };

  const selectedSlot = slots.find((s) => s.id === selectedSlotId);

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
      <Navbar />

      <main className="flex-1 mx-auto max-w-7xl w-full px-6 py-8">
        {/* Header Strip */}
        <div className="border-b border-[#EAEAE6] pb-6">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-[#0F172A]">Book an In-Person Site Visit</h1>
            <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-800 border border-emerald-200">
              Live Availability
            </span>
          </div>
          <p className="mt-1 text-xs text-[#64748B]">
            Schedule a private tour of sample apartments at Harmony Enclave or Skyline Serenity. 
            Backend validates real-time capacity and protects against double booking.
          </p>
        </div>

        {/* Project Selector Tabs */}
        <div className="mt-6 flex flex-wrap gap-3">
          {projects.map((proj: any) => (
            <button
              key={proj.id}
              onClick={() => handleProjectSelect(proj.id)}
              className={`flex items-center gap-2 rounded-xl px-5 py-3 text-xs font-bold transition border ${
                selectedProjectId === proj.id
                  ? "border-[#0F172A] bg-[#0F172A] text-white shadow-sm"
                  : "border-[#E2E8F0] bg-white text-[#334155] hover:border-emerald-500 hover:bg-emerald-50/30"
              }`}
            >
              <Building2 className={`h-4 w-4 ${selectedProjectId === proj.id ? "text-emerald-400" : "text-[#64748B]"}`} />
              <span>{proj.name}</span>
            </button>
          ))}
        </div>

        <div className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Interactive Slot Grid */}
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between border-b border-[#F1F5F9] pb-4">
                <div className="flex items-center gap-2">
                  <CalendarIcon className="h-4 w-4 text-emerald-600" />
                  <h2 className="text-sm font-bold text-[#0F172A]">Available Visit Slots (Next 10 Days)</h2>
                </div>
                <span className="text-[11px] text-[#64748B]">Max 3 parties per slot</span>
              </div>

              {loadingSlots ? (
                <div className="py-16 text-center text-xs text-[#64748B] flex items-center justify-center">
                  <Loader2 className="h-5 w-5 animate-spin text-emerald-600 mr-2" />
                  Loading real-time slot calendar...
                </div>
              ) : Object.keys(groupedSlots).length === 0 ? (
                <div className="py-12 text-center text-xs text-[#94A3B8]">
                  No upcoming slots found for this project.
                </div>
              ) : (
                <div className="mt-4 space-y-6">
                  {Object.entries(groupedSlots).map(([dateKey, daySlots]) => (
                    <div key={dateKey}>
                      <div className="text-xs font-bold uppercase tracking-wider text-[#64748B] mb-2.5">
                        {dateKey}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        {daySlots.map((s) => {
                          const isSelected = selectedSlotId === s.id;
                          const isFull = s.booked_count >= s.max_capacity;
                          const timeStr = new Date(s.slot_start).toLocaleTimeString("en-IN", {
                            hour: "2-digit",
                            minute: "2-digit",
                            hour12: true,
                          });

                          return (
                            <button
                              key={s.id}
                              type="button"
                              disabled={isFull}
                              onClick={() => setSelectedSlotId(s.id)}
                              className={`flex flex-col rounded-xl border p-3.5 text-left transition ${
                                isFull
                                  ? "border-slate-200 bg-slate-50 opacity-60 cursor-not-allowed"
                                  : isSelected
                                  ? "border-emerald-600 bg-emerald-50/70 ring-2 ring-emerald-500 shadow-sm"
                                  : "border-[#E2E8F0] bg-white hover:border-emerald-500 hover:bg-emerald-50/20"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                                  <Clock className="h-3.5 w-3.5 text-slate-400" />
                                  {timeStr}
                                </span>
                                {isFull ? (
                                  <span className="text-[10px] font-bold text-rose-700 bg-rose-50 px-1.5 py-0.5 rounded">
                                    Full
                                  </span>
                                ) : (
                                  <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded">
                                    {s.available_spots} open
                                  </span>
                                )}
                              </div>
                              <span className="mt-2 text-[10px] text-[#64748B]">
                                {isFull ? "No spots remaining" : `Capacity: ${s.booked_count}/${s.max_capacity} reserved`}
                              </span>
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Location & Directions Card */}
            <div className="rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-sm">
              <div className="flex items-center gap-2 border-b border-[#F1F5F9] pb-3">
                <MapPin className="h-4 w-4 text-emerald-600" />
                <h3 className="text-xs font-bold text-[#0F172A]">Site Location & Verified RERA</h3>
              </div>
              <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-[#94A3B8] font-medium">Project Address</span>
                  <p className="mt-1 font-semibold text-[#0F172A]">
                    {selectedProjectId === projects[0]?.id
                      ? "Harmony Enclave, Shela, Off Club O7 Road, Ahmedabad — 380058"
                      : "Skyline Serenity, SG Highway, Near Vaishno Devi Circle, Ahmedabad — 382421"}
                  </p>
                  <p className="mt-1 text-[11px] text-[#64748B]">
                    Dedicated visitor parking & EV charging bays available at site entrance.
                  </p>
                </div>
                <div>
                  <span className="text-[#94A3B8] font-medium">Statutory Gujarat RERA Number</span>
                  <p className="mt-1 font-mono font-bold text-emerald-800">
                    {selectedProjectId === projects[0]?.id
                      ? "PR/GJ/AHMEDABAD/AUDA/RAA09876/011124"
                      : "PR/GJ/AHMEDABAD/AHMEDABAD CITY/RAA08765/150824"}
                  </p>
                  <p className="mt-1 text-[11px] text-[#64748B]">
                    All marketing materials and floor plans match approved GujRERA records.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Reservation Form */}
          <div className="space-y-6">
            <div className="rounded-2xl border border-[#EAEAE6] bg-white p-6 shadow-sm sticky top-20">
              <h3 className="text-sm font-bold text-[#0F172A] border-b border-[#F1F5F9] pb-3">
                Reservation Details
              </h3>

              {bookingError && (
                <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-800 flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                  <span>{bookingError}</span>
                </div>
              )}

              {selectedSlot ? (
                <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50/60 p-3 text-xs">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-emerald-900">
                    Selected Visit Slot
                  </div>
                  <div className="mt-1 font-bold text-emerald-950">
                    {formatDateTime(selectedSlot.slot_start)}
                  </div>
                  <div className="text-[11px] text-emerald-800 mt-0.5">
                    {selectedSlot.project_name} ({selectedSlot.available_spots} spots remaining)
                  </div>
                </div>
              ) : (
                <div className="mt-4 rounded-xl border border-dashed border-[#CBD5E1] p-4 text-center text-xs text-[#94A3B8]">
                  Select an available slot from the calendar on the left
                </div>
              )}

              <form onSubmit={handleBookingSubmit} className="mt-5 space-y-3.5">
                <div>
                  <label className="block text-xs font-medium text-[#334155]">Full Name *</label>
                  <div className="relative mt-1">
                    <User className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
                    <input
                      type="text"
                      required
                      value={buyerName}
                      onChange={(e) => setBuyerName(e.target.value)}
                      placeholder="e.g. Gaurav Mehta"
                      className="w-full rounded-xl border border-[#CBD5E1] bg-white py-2 pl-9 pr-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#334155]">Phone Number *</label>
                  <div className="relative mt-1">
                    <Phone className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#94A3B8]" />
                    <input
                      type="text"
                      required
                      value={rawPhone}
                      onChange={(e) => setRawPhone(e.target.value)}
                      placeholder="+91 98250 00000"
                      className="w-full rounded-xl border border-[#CBD5E1] bg-white py-2 pl-9 pr-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                    />
                  </div>
                  <span className="text-[10px] text-[#94A3B8]">E.164 verified • DPDP consent compliant</span>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#334155]">Configuration of Interest</label>
                  <select
                    value={preferredBhk}
                    onChange={(e) => setPreferredBhk(e.target.value)}
                    className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                  >
                    <option value="2 BHK">2 BHK Apartment</option>
                    <option value="3 BHK">3 BHK Luxury Apartment</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-[#334155]">Special Preferences / Notes</label>
                  <textarea
                    rows={2}
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="e.g. Garden facing, high floor, Vaastu preference..."
                    className="mt-1 w-full rounded-xl border border-[#CBD5E1] bg-white py-2 px-3 text-xs text-[#0F172A] focus:border-emerald-600 focus:outline-none"
                  />
                </div>

                <button
                  type="submit"
                  disabled={bookingLoading || !selectedSlotId}
                  className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-[#059669] py-3 text-xs font-bold text-white shadow-sm hover:bg-[#047857] disabled:opacity-50 transition"
                >
                  {bookingLoading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin text-white" />
                      Acquiring Slot Lock & Confirming...
                    </>
                  ) : (
                    <>
                      Confirm Site Visit Booking
                      <ArrowRight className="h-4 w-4" />
                    </>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>

        {/* Confirmation Modal */}
        {confirmedBooking && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="w-full max-w-lg rounded-2xl border border-emerald-300 bg-white p-6 shadow-2xl">
              <div className="text-center">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700">
                  <CheckCircle2 className="h-7 w-7" />
                </div>
                <h3 className="mt-3 text-lg font-bold text-[#0F172A]">Site Visit Confirmed!</h3>
                <span className="mt-1 inline-block font-mono text-xs font-extrabold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
                  Ref: {confirmedBooking.booking_reference}
                </span>
              </div>

              <div className="mt-6 space-y-3 text-xs bg-[#F8FAFC] p-4 rounded-xl border border-[#F1F5F9]">
                <div className="flex justify-between border-b border-slate-200/60 pb-2">
                  <span className="text-[#64748B]">Project</span>
                  <span className="font-bold text-[#0F172A]">{confirmedBooking.project_name}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200/60 pb-2">
                  <span className="text-[#64748B]">Date & Time</span>
                  <span className="font-bold text-[#0F172A]">{formatDateTime(confirmedBooking.slot_start)}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200/60 pb-2">
                  <span className="text-[#64748B]">Location</span>
                  <span className="font-medium text-[#0F172A] text-right max-w-[240px]">{confirmedBooking.location}</span>
                </div>
                <div className="flex justify-between border-b border-slate-200/60 pb-2">
                  <span className="text-[#64748B]">Assigned Executive</span>
                  <span className="font-bold text-emerald-800">{confirmedBooking.assigned_salesperson_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#64748B]">Executive Direct Contact</span>
                  <span className="font-semibold text-[#0F172A]">{confirmedBooking.assigned_salesperson_phone}</span>
                </div>
              </div>

              {/* Reminder Dispatch Preview */}
              <div className="mt-4 flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50/70 p-3 text-xs text-emerald-900">
                <Bell className="h-4 w-4 shrink-0 text-emerald-600" />
                <span>
                  Automated reminders scheduled for <strong>1 day before</strong> and <strong>2 hours before</strong> via WhatsApp & SMS.
                </span>
              </div>

              <div className="mt-6 flex justify-end gap-3">
                <button
                  onClick={() => setConfirmedBooking(null)}
                  className="w-full rounded-xl bg-[#0F172A] py-2.5 text-xs font-semibold text-white hover:bg-[#1E293B]"
                >
                  Done & Return to Schedule
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
