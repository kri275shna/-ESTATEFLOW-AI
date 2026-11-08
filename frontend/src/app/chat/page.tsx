"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import { 
  Sparkles, Send, Calendar, UserCheck, ShieldCheck, 
  Building2, ArrowRight, Loader2, Phone, MapPin, 
  HelpCircle, MessageCircle, AlertCircle
} from "lucide-react";
import { getStoredUser, AuthUser } from "@/lib/auth";

interface ChatMessage {
  id: string;
  sender_type: "buyer" | "assistant" | "system";
  content: string;
  language?: string;
  is_uncertain?: boolean;
  action?: string;
  timestamp?: string;
}

const QUICK_PROMPTS = [
  "What are the 2 BHK & 3 BHK carpet areas?",
  "Tell me about the clubhouse and amenities",
  "What is the RERA registration and possession date?",
  "What is the starting price range?",
  "I want to schedule an in-person site visit",
  "Please have a sales executive call me",
];

export default function BuyerChatPage() {
  const router = useRouter();
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [sessionToken, setSessionToken] = useState<string | null>(null);
  const [language, setLanguage] = useState<"en" | "hi" | "gu">("en");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [handoffStatus, setHandoffStatus] = useState<string | null>(null);
  
  // Buyer Lead Info for Session Link
  const [buyerName, setBuyerName] = useState("Gaurav Mehta");
  const [buyerPhone, setBuyerPhone] = useState("+919825000099");
  const [selectedProject, setSelectedProject] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Initialize or resume chat session
  const initSession = async (lang = language) => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/chat/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          full_name: buyerName,
          phone: buyerPhone,
          preferred_language: lang,
          project_id: selectedProject,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setSessionToken(data.session_token);
        setMessages([
          {
            id: "msg-welcome",
            sender_type: "assistant",
            content: data.welcome_message,
            language: lang,
          },
        ]);
      }
    } catch (err) {
      console.error("Failed to init chat session", err);
    }
  };

  useEffect(() => {
    const user = getStoredUser();
    if (user) {
      setCurrentUser(user);
      setBuyerName(user.full_name);
      if (user.phone) setBuyerPhone(user.phone);
    }
    initSession();
  }, []);

  const handleLanguageChange = (newLang: "en" | "hi" | "gu") => {
    setLanguage(newLang);
    initSession(newLang);
  };

  // Send message
  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend || inputText;
    if (!text.trim() || !sessionToken || loading) return;

    const userMsg: ChatMessage = {
      id: `msg-user-${Date.now()}`,
      sender_type: "buyer",
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputText("");
    setLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/chat/sessions/${sessionToken}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: text,
          project_id: selectedProject,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        const assistantMsg: ChatMessage = {
          id: `msg-ai-${Date.now()}`,
          sender_type: "assistant",
          content: data.reply,
          language: data.language,
          is_uncertain: data.is_uncertain,
          action: data.action,
          timestamp: data.timestamp,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        if (data.action === "TRIGGER_HANDOFF") {
          setHandoffStatus("Dedicated sales executive assigned to your inquiry.");
        }
      }
    } catch (err) {
      console.error("Error sending message", err);
    } finally {
      setLoading(false);
    }
  };

  // Explicit Human Escalation
  const handleRequestHuman = async () => {
    if (!sessionToken) return;
    setLoading(true);

    try {
      const res = await fetch(`http://localhost:8000/api/v1/chat/sessions/${sessionToken}/handoff`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reason: "Buyer clicked 'Speak with Sales Executive' button in chat",
          buyer_name: buyerName,
          phone: buyerPhone,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setHandoffStatus(`Assigned to ${data.assigned_executive_name}. A representative will call you shortly.`);
        setMessages((prev) => [
          ...prev,
          {
            id: `msg-handoff-${Date.now()}`,
            sender_type: "assistant",
            content: `Thank you! I have assigned ${data.assigned_executive_name} from our senior sales team to assist you. They have received your full preferences and will reach out promptly. You can also pick a site visit slot below.`,
            action: "SHOW_BOOKING_SLOTS",
          },
        ]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col bg-[#FBFBFA]">
      <Navbar />

      <main className="flex-1 mx-auto max-w-5xl w-full px-4 py-6 sm:px-6">
        {/* Header Strip */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#EAEAE6] pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#0F172A] text-white shadow-sm">
              <Sparkles className="h-6 w-6 text-emerald-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-lg font-bold tracking-tight text-[#0F172A]">EstateFlow AI Concierge</h1>
                <span className="flex items-center gap-1 rounded bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-800 border border-emerald-200">
                  <ShieldCheck className="h-3 w-3 text-emerald-600" />
                  Fact-Sheet Grounded
                </span>
              </div>
              <p className="text-xs text-[#64748B]">
                Gujarat RERA verified property details for Company A developments in Shela & SG Highway.
              </p>
            </div>
          </div>

          {/* Controls: Language & Human Button */}
          <div className="flex items-center gap-2.5">
            {/* Language Switcher */}
            <div className="flex rounded-xl border border-[#CBD5E1] bg-white p-1 text-xs">
              <button
                onClick={() => handleLanguageChange("en")}
                className={`rounded-lg px-2.5 py-1 font-semibold transition ${
                  language === "en" ? "bg-[#0F172A] text-white" : "text-[#64748B] hover:text-[#0F172A]"
                }`}
              >
                English
              </button>
              <button
                onClick={() => handleLanguageChange("hi")}
                className={`rounded-lg px-2.5 py-1 font-semibold transition ${
                  language === "hi" ? "bg-[#0F172A] text-white" : "text-[#64748B] hover:text-[#0F172A]"
                }`}
              >
                हिन्दी
              </button>
              <button
                onClick={() => handleLanguageChange("gu")}
                className={`rounded-lg px-2.5 py-1 font-semibold transition ${
                  language === "gu" ? "bg-[#0F172A] text-white" : "text-[#64748B] hover:text-[#0F172A]"
                }`}
              >
                ગુજરાતી
              </button>
            </div>

            <button
              onClick={handleRequestHuman}
              className="flex items-center gap-1.5 rounded-xl border border-[#CBD5E1] bg-white px-3 py-1.5 text-xs font-semibold text-[#0F172A] hover:bg-[#F8FAFC] hover:border-emerald-600 transition"
            >
              <UserCheck className="h-3.5 w-3.5 text-emerald-600" />
              Speak to Salesperson
            </button>
          </div>
        </div>

        {/* Project Cards Selector */}
        <div className="my-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div
            onClick={() => setSelectedProject("PROJECT-1")}
            className={`cursor-pointer rounded-xl border p-3 transition ${
              selectedProject === "PROJECT-1"
                ? "border-emerald-600 bg-emerald-50/50 shadow-sm"
                : "border-[#EAEAE6] bg-white hover:border-[#CBD5E1]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#0F172A]">Harmony Enclave</span>
              <span className="text-[10px] font-bold text-emerald-800">₹65L – ₹95L</span>
            </div>
            <p className="mt-1 text-[11px] text-[#64748B]">Shela, Club O7 Road • 2 & 3 BHK • 20,000 sq ft Clubhouse</p>
          </div>

          <div
            onClick={() => setSelectedProject("PROJECT-2")}
            className={`cursor-pointer rounded-xl border p-3 transition ${
              selectedProject === "PROJECT-2"
                ? "border-emerald-600 bg-emerald-50/50 shadow-sm"
                : "border-[#EAEAE6] bg-white hover:border-[#CBD5E1]"
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-[#0F172A]">Skyline Serenity</span>
              <span className="text-[10px] font-bold text-emerald-800">₹85L – ₹1.20 Cr</span>
            </div>
            <p className="mt-1 text-[11px] text-[#64748B]">SG Highway, Near Vaishno Devi • 2 & 3 BHK Luxury • Sky Lounge</p>
          </div>
        </div>

        {/* Chat Stream Window */}
        <div className="rounded-2xl border border-[#EAEAE6] bg-white shadow-sm flex flex-col h-[520px]">
          {/* Messages list */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex flex-col ${m.sender_type === "buyer" ? "items-end" : "items-start"}`}
              >
                <div className="flex items-center gap-1.5 mb-1 text-[10px] text-[#94A3B8]">
                  <span>{m.sender_type === "buyer" ? buyerName : "EstateFlow Concierge"}</span>
                  {m.sender_type === "assistant" && (
                    <span className="rounded bg-emerald-50 text-emerald-700 font-bold px-1 py-0.2">Verified</span>
                  )}
                </div>

                <div
                  className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-xs leading-relaxed shadow-sm ${
                    m.sender_type === "buyer"
                      ? "bg-[#0F172A] text-white rounded-br-none"
                      : "bg-[#F8FAFC] text-[#0F172A] rounded-bl-none border border-[#E2E8F0]"
                  }`}
                >
                  <p className="whitespace-pre-wrap">{m.content}</p>

                  {/* Inline Action: Book Site Visit Callout */}
                  {(m.action === "SHOW_BOOKING_SLOTS" || m.action === "OFFER_SITE_VISIT") && (
                    <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50/80 p-3 text-xs">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Calendar className="h-4 w-4 text-emerald-700" />
                          <span className="font-bold text-emerald-950">Genuine Free Visit Slots Available</span>
                        </div>
                        <a
                          href="/book"
                          className="flex items-center gap-1 rounded-lg bg-[#059669] px-3 py-1.5 text-[11px] font-bold text-white shadow-sm hover:bg-[#047857] transition"
                        >
                          Book Visit Slot
                          <ArrowRight className="h-3 w-3" />
                        </a>
                      </div>
                      <p className="mt-1 text-[10px] text-emerald-800">
                        Select a date & time. Backend validates slot availability with double-booking prevention.
                      </p>
                    </div>
                  )}

                  {/* Flagged / Human Hand-off notification */}
                  {m.is_uncertain && (
                    <div className="mt-2 text-[10px] text-amber-800 flex items-center gap-1">
                      <AlertCircle className="h-3 w-3 shrink-0 text-amber-600" />
                      <span>Noted for Sales Head review and human executive confirmation.</span>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-xs text-[#64748B]">
                <div className="flex h-7 w-7 items-center justify-center rounded-xl bg-slate-100">
                  <Loader2 className="h-4 w-4 animate-spin text-emerald-600" />
                </div>
                <span>Checking approved fact sheet...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Reply Chips */}
          <div className="border-t border-[#F1F5F9] bg-[#FBFBFA] px-4 py-2.5 overflow-x-auto flex gap-2">
            {QUICK_PROMPTS.map((prompt, i) => (
              <button
                key={i}
                type="button"
                onClick={() => handleSendMessage(prompt)}
                disabled={loading}
                className="shrink-0 rounded-full border border-[#CBD5E1] bg-white px-3 py-1 text-[11px] font-medium text-[#475569] hover:border-emerald-600 hover:text-emerald-700 transition disabled:opacity-50"
              >
                {prompt}
              </button>
            ))}
          </div>

          {/* Input Box */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="border-t border-[#EAEAE6] bg-white p-3 flex items-center gap-2"
          >
            <input
              type="text"
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder={
                language === "gu"
                  ? "અહીં તમારી પૃચ્છા લખો (દા.ત. 3 BHK નો ભાવ શું છે?)..."
                  : language === "hi"
                  ? "यहाँ अपना प्रश्न लिखें (जैसे 2 BHK का कार्पेट एरिया क्या है?)..."
                  : "Type your property requirement or question..."
              }
              className="flex-1 rounded-xl border border-[#CBD5E1] bg-white py-2.5 px-4 text-xs text-[#0F172A] placeholder-[#94A3B8] focus:border-emerald-600 focus:outline-none focus:ring-1 focus:ring-emerald-600"
            />
            <button
              type="submit"
              disabled={loading || !inputText.trim()}
              className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#0F172A] text-white shadow-sm hover:bg-[#1E293B] disabled:opacity-50 transition shrink-0"
            >
              <Send className="h-4 w-4 text-emerald-400" />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
