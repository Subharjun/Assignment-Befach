import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage } from "@/lib/types";

type State = {
  open: boolean;
  sessionId: string;
  messages: ChatMessage[];
  isSending: boolean;
  isLoadingSession: boolean;
  pendingSpeech: string | null;
  setOpen: (v: boolean) => void;
  toggle: () => void;
  push: (m: ChatMessage) => void;
  setIsSending: (v: boolean) => void;
  setIsLoadingSession: (v: boolean) => void;
  setPendingSpeech: (text: string | null) => void;
  reset: () => void;
  newSession: () => void;
  loadSession: (sessionId: string, messages: ChatMessage[]) => void;
};

function newSession(): string {
  return typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);
}

export const useChat = create<State>()(
  persist(
    (set) => ({
      open: false,
      sessionId: newSession(),
      messages: [],
      isSending: false,
      isLoadingSession: false,
      pendingSpeech: null,
      setOpen: (v) => set({ open: v }),
      toggle: () => set((s) => ({ open: !s.open })),
      push: (m) => set((s) => ({ messages: [...s.messages, m] })),
      setIsSending: (v) => set({ isSending: v }),
      setIsLoadingSession: (v) => set({ isLoadingSession: v }),
      setPendingSpeech: (text) => set({ pendingSpeech: text }),
      reset: () => set({ messages: [], sessionId: newSession() }),
      newSession: () => set({ messages: [], sessionId: newSession() }),
      loadSession: (sessionId, messages) => set({ sessionId, messages }),
    }),
    { name: "ai-commerce-chat", partialize: (s) => ({ sessionId: s.sessionId, messages: s.messages }) }
  )
);
