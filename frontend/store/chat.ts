import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { ChatMessage } from "@/lib/types";

type State = {
  open: boolean;
  sessionId: string;
  messages: ChatMessage[];
  isSending: boolean;
  isLoadingSession: boolean;
  setOpen: (v: boolean) => void;
  toggle: () => void;
  push: (m: ChatMessage) => void;
  setIsSending: (v: boolean) => void;
  setIsLoadingSession: (v: boolean) => void;
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
      setOpen: (v) => set({ open: v }),
      toggle: () => set((s) => ({ open: !s.open })),
      push: (m) => set((s) => ({ messages: [...s.messages, m] })),
      setIsSending: (v) => set({ isSending: v }),
      setIsLoadingSession: (v) => set({ isLoadingSession: v }),
      reset: () => set({ messages: [], sessionId: newSession() }),
      newSession: () => set({ messages: [], sessionId: newSession() }),
      loadSession: (sessionId, messages) => set({ sessionId, messages }),
    }),
    { name: "ai-commerce-chat", partialize: (s) => ({ sessionId: s.sessionId, messages: s.messages }) }
  )
);
