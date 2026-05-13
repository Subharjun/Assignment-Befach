"use client";
import { cn } from "@/lib/cn";

export default function CategoryFilter({
  categories,
  active,
  onChange,
}: {
  categories: string[];
  active: string | null;
  onChange: (c: string | null) => void;
}) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-2 mb-4">
      <button
        onClick={() => onChange(null)}
        className={cn(
          "px-3 py-1.5 rounded-full text-sm whitespace-nowrap",
          active === null
            ? "bg-brand-600 text-white"
            : "bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20"
        )}
      >
        All
      </button>
      {categories.map((c) => (
        <button
          key={c}
          onClick={() => onChange(c)}
          className={cn(
            "px-3 py-1.5 rounded-full text-sm whitespace-nowrap",
            active === c
              ? "bg-brand-600 text-white"
              : "bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/20"
          )}
        >
          {c}
        </button>
      ))}
    </div>
  );
}
