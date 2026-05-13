"use client";
import { useEffect, useRef, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Search, MapPin } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/cn";

type Suggestion = {
  slug: string;
  title: string;
  image_url: string;
  price: number;
  category: string;
};

export default function SearchBar() {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(-1);
  const [loading, setLoading] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const reqId = useRef(0);

  useEffect(() => {
    const v = q.trim();
    if (v.length < 2) {
      setSuggestions([]);
      return;
    }
    setLoading(true);
    const myId = ++reqId.current;
    const t = setTimeout(() => {
      api
        .suggest(v, 6)
        .then((s) => {
          if (myId !== reqId.current) return;
          setSuggestions(s);
        })
        .catch(() => setSuggestions([]))
        .finally(() => myId === reqId.current && setLoading(false));
    }, 180);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false);
    }
    window.addEventListener("mousedown", onClick);
    return () => window.removeEventListener("mousedown", onClick);
  }, []);

  function submit(value?: string) {
    const term = (value ?? q).trim();
    if (!term) return;
    setOpen(false);
    router.push(`/search?q=${encodeURIComponent(term)}`);
  }

  function onKey(e: React.KeyboardEvent<HTMLInputElement>) {
    if (!open) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setHighlight((h) => Math.min(h + 1, suggestions.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setHighlight((h) => Math.max(h - 1, -1));
    } else if (e.key === "Enter") {
      if (highlight >= 0 && suggestions[highlight]) {
        e.preventDefault();
        router.push(`/products/${suggestions[highlight].slug}`);
        setOpen(false);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  }

  return (
    <div ref={wrapRef} className="relative flex-1 max-w-3xl">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
        className="flex h-10 rounded-md overflow-hidden shadow-sm ring-1 ring-transparent focus-within:ring-orange-400 transition"
      >
        <div className="hidden sm:flex items-center gap-1 px-3 bg-neutral-100 dark:bg-neutral-800 text-xs border-r border-black/10 dark:border-white/10">
          <MapPin className="w-3.5 h-3.5" /> All
        </div>
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
            setHighlight(-1);
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKey}
          placeholder="Search MayaMall"
          className="flex-1 px-3 bg-white text-neutral-900 focus:outline-none"
        />
        <button
          type="submit"
          aria-label="Search"
          className="px-4 bg-orange-400 hover:bg-orange-500 text-neutral-900 grid place-items-center"
        >
          <Search className="w-4 h-4" />
        </button>
      </form>

      {open && q.trim().length >= 2 && (
        <div className="absolute z-50 left-0 right-0 mt-1 rounded-md bg-white dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 shadow-2xl ring-1 ring-black/10 dark:ring-white/10 overflow-hidden animate-fade-in-up">
          {loading && suggestions.length === 0 && (
            <div className="px-4 py-3 text-sm opacity-70">Searching…</div>
          )}
          {!loading && suggestions.length === 0 && (
            <div className="px-4 py-3 text-sm opacity-70">No matches. Press Enter to search anyway.</div>
          )}
          {suggestions.map((s, i) => (
            <Link
              key={s.slug}
              href={`/products/${s.slug}`}
              onClick={() => setOpen(false)}
              className={cn(
                "flex items-center gap-3 px-3 py-2 text-sm hover:bg-neutral-100 dark:hover:bg-white/10",
                i === highlight && "bg-neutral-100 dark:bg-white/10"
              )}
            >
              <div className="relative w-10 h-10 rounded bg-neutral-100 overflow-hidden shrink-0">
                <Image src={s.image_url} alt="" fill className="object-cover" sizes="40px" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="truncate">{s.title}</div>
                <div className="text-[11px] opacity-60">{s.category}</div>
              </div>
              <div className="font-semibold whitespace-nowrap">
                ₹{s.price.toLocaleString("en-IN")}
              </div>
            </Link>
          ))}
          {suggestions.length > 0 && (
            <button
              type="button"
              onClick={() => submit()}
              className="block w-full text-left px-3 py-2 text-xs font-medium border-t border-black/10 dark:border-white/10 hover:bg-neutral-100 dark:hover:bg-white/10"
            >
              See all results for "{q}"
            </button>
          )}
        </div>
      )}
    </div>
  );
}
