import { create } from "zustand";
import { persist } from "zustand/middleware";

type Theme = "light" | "dark";

type State = {
  theme: Theme;
  toggle: () => void;
  apply: () => void;
};

export const useTheme = create<State>()(
  persist(
    (set, get) => ({
      theme: "light",
      toggle: () => {
        const next: Theme = get().theme === "dark" ? "light" : "dark";
        set({ theme: next });
        if (typeof document !== "undefined") {
          document.documentElement.classList.toggle("dark", next === "dark");
        }
      },
      apply: () => {
        if (typeof document !== "undefined") {
          document.documentElement.classList.toggle("dark", get().theme === "dark");
        }
      },
    }),
    { name: "ai-commerce-theme" }
  )
);
