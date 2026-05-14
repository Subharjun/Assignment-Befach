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

type Session = { session_id: string; preview: string; updated_at: string | null };

export default function VoiceAssistant() {
  const { open, setOpen, sessionId, messages, push, isSending, setIsSending, isLoadingSession, setIsLoadingSession, newSession, loadSession, pendingSpeech, setPendingSpeech } = useChat();
  const { getToken } = useAuth();
  const { isSignedIn } = useUser();

  const [supported, setSupported] = useState(true);
  const [recording, setRecording] = useState(false);
  const [transcribing, setTranscribing] = useState(false);
  const [recTime, setRecTime] = useState(0);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const voicesRef = useRef<SpeechSynthesisVoice[]>([]);

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
    setSupported(typeof navigator !== "undefined" && Boolean(navigator.mediaDevices?.getUserMedia));
  }, []);

  // Pre-load voices so speak() can set one explicitly (Chrome returns [] on first call).
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    const load = () => { voicesRef.current = window.speechSynthesis.getVoices(); };
    load();
    window.speechSynthesis.addEventListener("voiceschanged", load);
    return () => window.speechSynthesis.removeEventListener("voiceschanged", load);
  }, []);

  useEffect(() => {
    if (scrollRef.current)
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, open]);

  const speak = useCallback(
    (text: string, retryCount = 0) => {
      if (!ttsEnabled || typeof window === "undefined" || !("speechSynthesis" in window)) {
        console.log("[Maya TTS] ❌ speak() blocked — ttsEnabled:", ttsEnabled, "window:", typeof window, "api:", "speechSynthesis" in window);
        return;
      }
      const synth = window.speechSynthesis;
      const clean = text.replace(/[*_`#]/g, "").trim();
      if (!clean) return;
      console.log("[Maya TTS] 🔊 speak() called:", clean.substring(0, 60), "| retryCount:", retryCount);

      // Cancel any in-flight speech first
      if (synth.speaking || synth.pending) {
        console.log("[Maya TTS] cancel() — was speaking:", synth.speaking, "pending:", synth.pending);
        synth.cancel();
      }

      const doSpeak = (attempt: number) => {
        // Safety: if still busy, wait and retry
        if (synth.speaking || synth.pending) {
          if (attempt < 10) {
            console.log("[Maya TTS] ⏳ still busy, retry attempt", attempt);
            setTimeout(() => doSpeak(attempt + 1), 80);
          }
          return;
        }

        // NEVER call resume() when nothing is queued — it corrupts Chrome's engine state
        const voices = voicesRef.current.length > 0 ? voicesRef.current : synth.getVoices();
        const pick =
          voices.find((v) => v.lang === "en-US") ||
          voices.find((v) => v.lang.startsWith("en")) ||
          voices[0];
        console.log("[Maya TTS] 🎙 voices available:", voices.length, "| chosen:", pick?.name ?? "NONE", pick?.lang ?? "");

        const u = new SpeechSynthesisUtterance(clean);
        u.volume = 1;
        u.rate = 1.0;
        u.pitch = 1.0;
        if (pick) u.voice = pick;

        // Keep-alive: Chrome hard-stops TTS after ~15 s on a single utterance
        let keepAlive: ReturnType<typeof setInterval> | null = null;
        u.onstart = () => {
          console.log("[Maya TTS] ✅ onstart — speech began");
          keepAlive = setInterval(() => {
            if (!synth.speaking) {
              if (keepAlive) clearInterval(keepAlive);
            } else if (synth.paused) {
              synth.resume();
            }
          }, 4000);
        };

        u.onend = () => {
          console.log("[Maya TTS] ✅ onend — speech finished");
          if (keepAlive) clearInterval(keepAlive);
        };

        u.onerror = (evt) => {
          if (keepAlive) clearInterval(keepAlive);
          // 'interrupted' happens when cancel() races with speak() — retry once
          if (evt.error === "interrupted" && retryCount < 2) {
            console.warn("[Maya TTS] interrupted — retrying", retryCount + 1);
            setTimeout(() => speak(text, retryCount + 1), 300);
          } else if (evt.error !== "canceled") {
            console.warn("[Maya TTS] ❌ onerror:", evt.error);
          }
        };

        console.log("[Maya TTS] 🔈 calling synth.speak() now");
        synth.speak(u);
        console.log("[Maya TTS]   → after speak(): speaking=", synth.speaking, "pending=", synth.pending);
      };

      // Give cancel() time to drain — poll instead of fixed timeout
      setTimeout(() => doSpeak(0), 100);
    },
    [ttsEnabled]
  );

  /* Speak text queued from outside this component (e.g. product page "Ask Maya" button) */
  useEffect(() => {
    if (pendingSpeech) {
      speak(pendingSpeech);
      setPendingSpeech(null);
    }
  }, [pendingSpeech, speak, setPendingSpeech]);

  const sendToMaya = useCallback(
    async (text: string) => {
      if (!text.trim() || isSending) return;
      if (!isSignedIn) {
        const authMsg = "Please sign in so I can remember your preferences across visits.";
        push({ role: "assistant", content: authMsg });
        speak(authMsg);
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

  const startRecording = useCallback(async () => {
    if (!supported) return;
    setError(null);
    chunksRef.current = [];
    if (typeof window !== "undefined") window.speechSynthesis?.cancel();

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      setError("Microphone blocked. Click the 🔒 in your address bar → allow Microphone → refresh.");
      return;
    }

    const mimeType = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : "audio/webm";
    const recorder = new MediaRecorder(stream, { mimeType });
    recorder.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data); };
    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      setRecording(false);
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
      setRecTime(0);

      const blob = new Blob(chunksRef.current, { type: mimeType });
      if (blob.size < 1000) return; // too short to transcribe
      setTranscribing(true);
      try {
        const { text } = await api.transcribe(blob);
        if (text.trim()) void sendToMaya(text.trim());
      } catch {
        setError("Transcription failed — check your connection and try again.");
      } finally {
        setTranscribing(false);
      }
    };

    mediaRecorderRef.current = recorder;
    recorder.start(250);
    setRecording(true);
    setRecTime(0);
    timerRef.current = setInterval(() => setRecTime((t) => t + 1), 1000);
  }, [supported, sendToMaya]);

  const stopRecording = useCallback(() => {
    try {
      mediaRecorderRef.current?.stop?.();
    } catch {
      setRecording(false);
    }
  }, []);

  return (
    <>
      {/* Floating mic launcher */}
      <button
        onClick={() => setOpen(true)}
        aria-label="Open Maya"
        className={cn(
          "fixed bottom-5 right-5 z-30 rounded-full shadow-xl p-4 bg-violet-600 text-white hover:bg-violet-500 transition",
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
            <div className="w-8 h-8 rounded-full bg-violet-600 text-white grid place-items-center">
              <Mic className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-semibold">Maya — voice assistant</div>
              <div className="text-[11px] opacity-60">
                {recording ? `Recording… ${recTime}s` : transcribing ? "Transcribing…" : "Tap the mic and speak"}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-1">
            <button onClick={startNewChat} title="Start a new chat" className="p-2 rounded hover:bg-black/5 dark:hover:bg-white/10">
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
              className={cn("p-2 rounded hover:bg-black/5 dark:hover:bg-white/10", showHistory && "bg-black/5 dark:bg-white/10")}
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
            <button onClick={() => setOpen(false)} className="p-2 rounded hover:bg-black/5 dark:hover:bg-white/10">
              <X className="w-4 h-4" />
            </button>
          </div>

          {showHistory && (
            <div className="absolute top-full right-3 mt-1 w-80 max-h-96 overflow-y-auto bg-white dark:bg-neutral-900 border border-black/10 dark:border-white/10 rounded-md shadow-2xl z-10">
              <div className="px-3 py-2 text-xs font-semibold uppercase tracking-wide opacity-70 border-b border-black/10 dark:border-white/10">
                Past conversations
              </div>
              {loadingSessions && <div className="px-3 py-3 text-sm opacity-60">Loading…</div>}
              {!loadingSessions && sessions.length === 0 && (
                <div className="px-3 py-3 text-sm opacity-60">No conversations yet.</div>
              )}
              {sessions.map((s) => (
                <div
                  key={s.session_id}
                  className={cn(
                    "group flex items-stretch border-b border-black/5 dark:border-white/5 hover:bg-black/5 dark:hover:bg-white/10",
                    s.session_id === sessionId && "bg-violet-50 dark:bg-violet-600/10"
                  )}
                >
                  <button onClick={() => openSession(s.session_id)} className="flex-1 text-left px-3 py-2 text-sm min-w-0">
                    <div className="line-clamp-2 break-words">{s.preview}</div>
                    {s.updated_at && (
                      <div className="text-[10px] opacity-50 mt-0.5">{new Date(s.updated_at).toLocaleString()}</div>
                    )}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); void deleteOneSession(s.session_id); }}
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
              <span className="inline-block w-3 h-3 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
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
          {recording && (
            <div className="self-end ml-auto max-w-[85%] px-3 py-2 rounded-2xl text-sm bg-red-100 dark:bg-red-500/20 italic opacity-80">
              Recording… {recTime}s — tap mic to send
            </div>
          )}
          {transcribing && (
            <div className="self-end ml-auto max-w-[85%] px-3 py-2 rounded-2xl text-sm bg-violet-100 dark:bg-violet-500/20 italic opacity-80">
              Transcribing…
            </div>
          )}
          {isSending && <TypingDots />}
        </div>

        {error && (
          <div className="px-4 py-2 text-xs text-red-700 dark:text-red-300 bg-red-50 dark:bg-red-900/30 border-t border-red-200 dark:border-red-900/50 flex items-start justify-between gap-2">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="opacity-70 hover:opacity-100" aria-label="Dismiss">
              <X className="w-3 h-3" />
            </button>
          </div>
        )}

        <div className="border-t border-black/10 dark:border-white/10 p-4 flex flex-col items-center gap-3">
          {/* Always-visible text input */}
          <FallbackInput onSend={sendToMaya} disabled={isSending} />

          {/* Mic — shown when browser supports speech */}
          {supported && (
            <div className="flex flex-col items-center gap-1 w-full">
              <div className="flex items-center gap-3 w-full">
                <div className="flex-1 h-px bg-black/10 dark:bg-white/10" />
                <span className="text-[11px] opacity-50">or speak</span>
                <div className="flex-1 h-px bg-black/10 dark:bg-white/10" />
              </div>
              <button
                onClick={recording ? stopRecording : () => void startRecording()}
                disabled={transcribing || isSending}
                aria-label={recording ? "Stop recording" : "Start recording"}
                className={cn(
                  "relative w-20 h-20 rounded-full grid place-items-center text-white shadow-xl transition disabled:opacity-50",
                  recording ? "bg-red-500 hover:bg-red-600" : "bg-violet-600 hover:bg-violet-500"
                )}
              >
                {recording ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
                {recording && (
                  <>
                    <span className="absolute inset-0 rounded-full bg-red-500/40 animate-ping" />
                    <span className="absolute inset-[-8px] rounded-full bg-red-500/20 animate-ping [animation-delay:200ms]" />
                  </>
                )}
              </button>
              <div className="text-xs opacity-70 text-center">
                {recording ? "Recording — tap again when done speaking" : "Tap to talk to Maya"}
              </div>
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

function FallbackInput({ onSend, disabled }: { onSend: (t: string) => void; disabled: boolean }) {
  const [v, setV] = useState("");
  return (
    <div className="w-full">
      <form
        onSubmit={(e) => { e.preventDefault(); if (v.trim()) { onSend(v); setV(""); } }}
        className="flex gap-2"
      >
        <input
          value={v}
          onChange={(e) => setV(e.target.value)}
          placeholder="Type a message to Maya…"
          className="flex-1 px-4 py-2.5 rounded-full bg-black/5 dark:bg-white/10 focus:outline-none focus:ring-2 focus:ring-violet-500 text-sm"
        />
        <button
          type="submit"
          disabled={disabled || !v.trim()}
          className="px-4 py-2 rounded-full bg-violet-600 text-white disabled:opacity-40 hover:bg-violet-500 transition text-sm font-medium"
        >
          Send
        </button>
      </form>
    </div>
  );
}

function Bubble({ role, content, products }: { role: "user" | "assistant"; content: string; products: Product[] }) {
  const isUser = role === "user";
  return (
    <div className={cn("flex flex-col gap-2", isUser ? "items-end" : "items-start")}>
      <div
        className={cn(
          "max-w-[85%] px-3 py-2 rounded-2xl text-sm whitespace-pre-wrap animate-fade-in-up",
          isUser ? "bg-violet-600 text-white rounded-br-sm" : "bg-black/5 dark:bg-white/10 rounded-bl-sm"
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
                <div className="text-xs font-semibold mt-1">₹{p.price.toLocaleString("en-IN")}</div>
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
