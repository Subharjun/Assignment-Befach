"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth, useUser } from "@clerk/nextjs";
import { Mic, MicOff, X, Volume2, VolumeX, MessageSquarePlus, History, Trash2 } from "lucide-react";
import Image from "next/image";
import Link from "next/link";
import { useChat } from "@/store/chat";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import { cn } from "@/lib/cn";

/* Browsers expose SpeechRecognition under prefixed names. */
function getSpeechRecognition(): any {
  if (typeof window === "undefined") return null;
  const w = window as any;
  return w.SpeechRecognition || w.webkitSpeechRecognition || null;
}

type Session = { session_id: string; preview: string; updated_at: string | null };

export default function VoiceAssistant() {
  const { open, setOpen, sessionId, messages, push, isSending, setIsSending, isLoadingSession, setIsLoadingSession, newSession, loadSession } = useChat();
  const { getToken } = useAuth();
  const { isSignedIn } = useUser();

  const [supported, setSupported] = useState(true);
  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState("");
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const recogRef = useRef<any>(null);
  const finalRef = useRef<string>("");
  const wantListenRef = useRef<boolean>(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  async function refreshSessions() {
    if (!isSignedIn) return;
    setLoadingSessions(true);
    try {
      const token = (await getToken()) ?? "";
      const list = await api.listSessions(token);
      setSessions(list);
    } catch {
      setSessions([]);
    } finally {
      setLoadingSessions(false);
    }
  }

  async function openSession(sid: string) {
    setShowHistory(false);
    setError(null);
    setIsLoadingSession(true);
    // Clear current messages immediately so the user sees the panel reset.
    loadSession(sid, []);
    try {
      const token = (await getToken()) ?? "";
      const convo = await api.getConversation(sid, token);
      const msgs = (convo.messages || [])
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({
          role: m.role as "user" | "assistant",
          content: m.content,
          products: (m.products as any) ?? [],
        }));
      loadSession(sid, msgs);
    } catch (e: any) {
      setError(`Couldn't load that conversation${e?.message ? `: ${e.message}` : "."}`);
    } finally {
      setIsLoadingSession(false);
    }
  }

  async function deleteOneSession(sid: string) {
    if (!window.confirm("Delete this conversation? This cannot be undone.")) return;
    try {
      const token = (await getToken()) ?? "";
      await api.deleteSession(sid, token);
      setSessions((prev) => prev.filter((s) => s.session_id !== sid));
      // If the deleted session is the current one, start a fresh chat.
      if (sid === sessionId) newSession();
    } catch {
      setError("Couldn't delete that conversation.");
    }
  }

  function startNewChat() {
    setShowHistory(false);
    newSession();
    if (typeof window !== "undefined") window.speechSynthesis?.cancel();
  }

  useEffect(() => {
    setSupported(Boolean(getSpeechRecognition()));
  }, []);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, open, interim]);

  const speak = useCallback(
    (text: string) => {
      if (!ttsEnabled || typeof window === "undefined" || !("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text.replace(/[*_`#]/g, ""));
      u.rate = 1.02;
      u.pitch = 1.0;
      window.speechSynthesis.speak(u);
    },
    [ttsEnabled]
  );

  const sendToMaya = useCallback(
    async (text: string) => {
      if (!text.trim() || isSending) return;
      if (!isSignedIn) {
        push({
          role: "assistant",
          content: "Please sign in so I can remember your preferences across visits.",
        });
        speak("Please sign in so I can remember your preferences.");
        return;
      }
      push({ role: "user", content: text });
      setIsSending(true);
      try {
        const token = (await getToken()) ?? "";
        const res = await api.chat(sessionId, text, token);
        push({ role: "assistant", content: res.reply, products: res.products });
        speak(res.reply);
      } catch {
        const msg = "Sorry, I couldn't reach the assistant.";
        push({ role: "assistant", content: msg });
        speak(msg);
      } finally {
        setIsSending(false);
      }
    },
    [getToken, isSending, isSignedIn, push, sessionId, setIsSending, speak]
  );

  const startListening = useCallback(() => {
    const Ctor = getSpeechRecognition();
    if (!Ctor) {
      setSupported(false);
      return;
    }
    setError(null);
    setInterim("");
    finalRef.current = "";
    wantListenRef.current = true;

    const recog = new Ctor();
    recog.lang = "en-IN";
    recog.interimResults = true;
    recog.continuous = true;          // stay listening through pauses
    recog.maxAlternatives = 1;

    recog.onresult = (e: any) => {
      let interimText = "";
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) finalRef.current += r[0].transcript + " ";
        else interimText += r[0].transcript;
      }
      setInterim(interimText);
    };
    recog.onerror = (e: any) => {
      // "no-speech" / "aborted" can fire from continuous mode after long silence;
      // ignore them so the mic doesn't appear to break.
      if (e.error === "no-speech" || e.error === "aborted") return;
      const msg =
        e.error === "not-allowed"
          ? "Microphone access denied. Allow it in your browser."
          : `Voice error: ${e.error}`;
      setError(msg);
      wantListenRef.current = false;
      setListening(false);
    };
    recog.onend = () => {
      setInterim("");
      // Browser ended the session (timeout, silence). If the user still wants
      // to listen, transparently restart. Only finalize when user clicked stop.
      if (wantListenRef.current) {
        try {
          recog.start();
        } catch {
          setListening(false);
        }
        return;
      }
      setListening(false);
      const text = finalRef.current.trim();
      finalRef.current = "";
      if (text) void sendToMaya(text);
    };

    recogRef.current = recog;
    setListening(true);
    if (typeof window !== "undefined") window.speechSynthesis?.cancel();
    recog.start();
  }, [sendToMaya]);

  const stopListening = useCallback(() => {
    // Signal "don't restart on onend", then stop. onend will send finalRef.
    wantListenRef.current = false;
    try {
      recogRef.current?.stop?.();
    } catch {
      setListening(false);
    }
  }, []);

  return (
    <>
      {/* Floating mic launcher */}
      <button
        onClick={() => setOpen(true)}
        aria-label="Open Maya"
        className={cn(
          "fixed bottom-5 right-5 z-30 rounded-full shadow-xl p-4 bg-orange-400 text-neutral-900 hover:bg-orange-500 transition",
          open && "scale-0 opacity-0 pointer-events-none"
        )}
      >
        <Mic className="w-5 h-5" />
      </button>

      {/* Backdrop */}
      <div
        onClick={() => setOpen(false)}
        className={cn(
          "fixed inset-0 z-40 bg-black/40 backdrop-blur-sm transition-opacity",
          open ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
      />

      {/* Panel */}
      <aside
        className={cn(
          "fixed top-0 right-0 z-50 h-full w-full sm:w-[440px] bg-white dark:bg-neutral-950 border-l border-black/10 dark:border-white/10 shadow-2xl flex flex-col transition-transform duration-300",
          open ? "translate-x-0" : "translate-x-full"
        )}
      >
        <header className="h-14 flex items-center justify-between px-4 border-b border-black/10 dark:border-white/10 relative">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-orange-400 text-neutral-900 grid place-items-center">
              <Mic className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-semibold">Maya — voice assistant</div>
              <div className="text-[11px] opacity-60">
                {listening ? "Listening…" : "Tap the mic and speak"}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={startNewChat}
              title="Start a new chat"
              className="p-2 rounded hover:bg-black/5 dark:hover:bg-white/10"
            >
              <MessageSquarePlus className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                setShowHistory((v) => {
                  const next = !v;
                  if (next) void refreshSessions();
                  return next;
                });
              }}
              title="Past conversations"
              className={cn(
                "p-2 rounded hover:bg-black/5 dark:hover:bg-white/10",
                showHistory && "bg-black/5 dark:bg-white/10"
              )}
            >
              <History className="w-4 h-4" />
            </button>
            <button
              onClick={() => setTtsEnabled((v) => !v)}
              title={ttsEnabled ? "Mute Maya's voice" : "Unmute Maya's voice"}
              className="p-2 rounded hover:bg-black/5 dark:hover:bg-white/10"
            >
              {ttsEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setOpen(false)}
              className="p-2 rounded hover:bg-black/5 dark:hover:bg-white/10"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {showHistory && (
            <div className="absolute top-full right-3 mt-1 w-80 max-h-96 overflow-y-auto bg-white dark:bg-neutral-900 border border-black/10 dark:border-white/10 rounded-md shadow-2xl z-10">
              <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wide opacity-70 border-b border-black/10 dark:border-white/10">
                Past conversations
              </div>
              {loadingSessions && (
                <div className="px-3 py-3 text-sm opacity-60">Loading…</div>
              )}
              {!loadingSessions && sessions.length === 0 && (
                <div className="px-3 py-3 text-sm opacity-60">No conversations yet.</div>
              )}
              {sessions.map((s) => (
                <div
                  key={s.session_id}
                  className={cn(
                    "group flex items-stretch border-b border-black/5 dark:border-white/5 hover:bg-black/5 dark:hover:bg-white/10",
                    s.session_id === sessionId && "bg-orange-50 dark:bg-orange-400/10"
                  )}
                >
                  <button
                    onClick={() => openSession(s.session_id)}
                    className="flex-1 text-left px-3 py-2 text-sm min-w-0"
                  >
                    <div className="line-clamp-2 break-words">{s.preview}</div>
                    {s.updated_at && (
                      <div className="text-[10px] opacity-50 mt-0.5">
                        {new Date(s.updated_at).toLocaleString()}
                      </div>
                    )}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      void deleteOneSession(s.session_id);
                    }}
                    title="Delete this conversation"
                    aria-label="Delete conversation"
                    className="px-3 grid place-items-center opacity-40 hover:opacity-100 hover:text-red-600 transition"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </header>

        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {isLoadingSession && (
            <div className="text-sm opacity-70 flex items-center gap-2">
              <span className="inline-block w-3 h-3 rounded-full border-2 border-orange-500 border-t-transparent animate-spin" />
              Loading conversation…
            </div>
          )}
          {!isLoadingSession && messages.length === 0 && (
            <div className="text-sm opacity-80 leading-relaxed">
              Hi! I'm Maya. Tap the mic and tell me what you're shopping for.
              <ul className="mt-3 space-y-1 text-xs opacity-80">
                <li>• "Find me a gaming laptop under 1.5 lakh"</li>
                <li>• "Show me running shoes for daily training"</li>
                <li>• "I need wireless noise-cancelling headphones"</li>
              </ul>
            </div>
          )}
          {messages.map((m, i) => (
            <Bubble key={i} role={m.role} content={m.content} products={m.products ?? []} />
          ))}
          {interim && (
            <div className="self-end ml-auto max-w-[85%] px-3 py-2 rounded-2xl text-sm bg-orange-100 dark:bg-orange-400/20 italic opacity-80">
              {interim}…
            </div>
          )}
          {isSending && <TypingDots />}
        </div>
        {error && (
          <div className="px-4 py-2 text-xs text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/30 border-t border-red-200 dark:border-red-900/50 flex items-start justify-between gap-2">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="opacity-70 hover:opacity-100"
              aria-label="Dismiss"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        <div className="border-t border-black/10 dark:border-white/10 p-4 flex flex-col items-center gap-2">
          {!supported ? (
            <FallbackInput onSend={sendToMaya} disabled={isSending} />
          ) : (
            <>
              <button
                onClick={listening ? stopListening : startListening}
                aria-label={listening ? "Stop" : "Start"}
                className={cn(
                  "relative w-20 h-20 rounded-full grid place-items-center text-white shadow-xl transition",
                  listening
                    ? "bg-red-500 hover:bg-red-600"
                    : "bg-orange-500 hover:bg-orange-600"
                )}
              >
                {listening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                {listening && (
                  <>
                    <span className="absolute inset-0 rounded-full bg-red-500/40 animate-ping" />
                    <span className="absolute inset-[-8px] rounded-full bg-red-500/20 animate-ping [animation-delay:200ms]" />
                  </>
                )}
              </button>
              <div className="text-xs opacity-70 text-center">
                {listening
                  ? "Listening — tap the mic again when you're done speaking"
                  : "Tap to talk to Maya"}
              </div>
            </>
          )}
        </div>
      </aside>
    </>
  );
}

function FallbackInput({
  onSend,
  disabled,
}: {
  onSend: (t: string) => void;
  disabled: boolean;
}) {
  const [v, setV] = useState("");
  return (
    <div className="w-full">
      <div className="text-[11px] opacity-70 mb-2 text-center">
        Your browser doesn't support voice input. Use text instead.
      </div>
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onSend(v);
          setV("");
        }}
        className="flex gap-2"
      >
        <input
          value={v}
          onChange={(e) => setV(e.target.value)}
          placeholder="Ask Maya…"
          className="flex-1 px-3 py-2 rounded-full bg-black/5 dark:bg-white/10 focus:outline-none focus:ring-2 focus:ring-orange-400"
        />
        <button
          type="submit"
          disabled={disabled}
          className="px-4 py-2 rounded-full bg-orange-500 text-white disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function Bubble({
  role,
  content,
  products,
}: {
  role: "user" | "assistant";
  content: string;
  products: Product[];
}) {
  const isUser = role === "user";
  return (
    <div className={cn("flex flex-col gap-2", isUser ? "items-end" : "items-start")}>
      <div
        className={cn(
          "max-w-[85%] px-3 py-2 rounded-2xl text-sm whitespace-pre-wrap animate-fade-in-up",
          isUser
            ? "bg-orange-500 text-white rounded-br-sm"
            : "bg-black/5 dark:bg-white/10 rounded-bl-sm"
        )}
      >
        {content}
      </div>
      {!isUser && products.length > 0 && (
        <div className="w-full grid grid-cols-2 gap-2 pr-2">
          {products.slice(0, 4).map((p) => (
            <Link
              key={p.slug}
              href={`/products/${p.slug}`}
              className="rounded-xl border border-black/10 dark:border-white/10 overflow-hidden hover:shadow-md transition bg-white dark:bg-white/[0.03]"
            >
              <div className="relative aspect-square">
                <Image src={p.image_url} alt={p.title} fill className="object-cover" sizes="200px" />
              </div>
              <div className="p-2">
                <div className="text-[11px] line-clamp-2">{p.title}</div>
                <div className="text-xs font-semibold mt-1">
                  ₹{p.price.toLocaleString("en-IN")}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-3 py-2 rounded-2xl bg-black/5 dark:bg-white/10 w-fit">
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-bounce [animation-delay:-0.2s]" />
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-bounce [animation-delay:-0.1s]" />
      <span className="w-1.5 h-1.5 rounded-full bg-current opacity-60 animate-bounce" />
    </div>
  );
}
