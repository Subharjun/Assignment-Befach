"use client";
import { useEffect, useMemo, useState } from "react";
import { Mic } from "lucide-react";
import { useChat } from "@/store/chat";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import ProductGrid from "@/components/ProductGrid";
import ProductRow from "@/components/ProductRow";
import CategoryFilter from "@/components/CategoryFilter";
import { GridSkeleton } from "@/components/Skeleton";

const SHELVES = [
  { title: "Best of Laptops", q: "Laptops" },
  { title: "Top picks in Audio", q: "Audio" },
  { title: "Trending Smartphones", q: "Mobiles" },
  { title: "Fashion finds", q: "Footwear" },
];

export default function HomePage() {
  const [categories, setCategories] = useState<string[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [products, setProducts] = useState<Product[] | null>(null);
  const [shelves, setShelves] = useState<Record<string, Product[]>>({});
  const setVoiceOpen = useChat((s) => s.setOpen);

  useEffect(() => {
    void api.listCategories().then(setCategories).catch(() => setCategories([]));
    SHELVES.forEach((s) => {
      void api
        .listProducts(s.q, 1, 5, "rating")
        .then((r) => setShelves((prev) => ({ ...prev, [s.q]: r.items })))
        .catch(() => {});
    });
  }, []);

  useEffect(() => {
    setProducts(null);
    void api
      .listProducts(active ?? undefined)
      .then((r) => setProducts(r.items))
      .catch(() => setProducts([]));
  }, [active]);

  const tiles = useMemo(
    () => [
      { title: "Laptops & Gaming", q: "Laptops", img: "https://images.unsplash.com/photo-1593642632559-0c6d3fc62b89?w=600" },
      { title: "Mobiles you'll love", q: "Mobiles", img: "https://images.unsplash.com/photo-1592286927505-1def25115558?w=600" },
      { title: "Home & Kitchen", q: "Kitchen", img: "https://images.unsplash.com/photo-1574781330855-d0db8cc6a79c?w=600" },
      { title: "Fashion edit", q: "Footwear", img: "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=600" },
    ],
    []
  );

  return (
    <div className="space-y-4 -mx-4 sm:mx-0">
      {/* Hero banner */}
      <section className="relative h-48 sm:h-72 overflow-hidden bg-gradient-to-br from-[#1e0048] via-[#3b0764] to-[#5b21b6] text-white">
        <div className="absolute inset-0 opacity-40 bg-[radial-gradient(circle_at_20%_50%,rgba(167,139,250,0.5),transparent_55%)]" />
        <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_80%_20%,rgba(139,92,246,0.6),transparent_50%)]" />
        <div className="mx-auto max-w-7xl px-4 h-full flex items-center justify-between relative">
          <div className="max-w-xl">
            <div className="text-xs uppercase tracking-widest text-violet-300 font-medium">AI Shopping — voice first</div>
            <h1 className="mt-2 text-2xl sm:text-4xl font-bold leading-tight">
              Tell Maya what you need.<br/> She'll walk you to it.
            </h1>
            <p className="mt-2 text-sm text-white/70 hidden sm:block">One World. Endless Choices. Powered by AI.</p>
            <button
              onClick={() => setVoiceOpen(true)}
              className="mt-4 inline-flex items-center gap-2 bg-violet-500 hover:bg-violet-400 text-white px-5 py-2.5 rounded-full font-semibold shadow-lg shadow-violet-900/50 transition"
            >
              <Mic className="w-4 h-4" /> Talk to Maya
            </button>
          </div>
          <div className="hidden md:block text-8xl opacity-20 select-none">✦</div>
        </div>
      </section>

      {/* Category tiles */}
      <section className="mx-auto max-w-7xl px-4 grid grid-cols-2 lg:grid-cols-4 gap-3">
        {tiles.map((t) => (
          <a
            key={t.q}
            href={`/category/${encodeURIComponent(t.q)}`}
            className="bg-white dark:bg-[#160030] rounded-xl p-4 shadow-sm border border-violet-100 dark:border-violet-900/40 hover:shadow-lg hover:border-violet-300 dark:hover:border-violet-700 transition"
          >
            <div className="font-semibold text-sm sm:text-base">{t.title}</div>
            <div className="relative w-full aspect-[4/3] mt-3 rounded-lg overflow-hidden bg-violet-50 dark:bg-violet-950/30">
              <img src={t.img} alt={t.title} className="w-full h-full object-cover" />
            </div>
            <div className="mt-2 text-xs text-violet-600 dark:text-violet-400 font-medium hover:underline">Shop now →</div>
          </a>
        ))}
      </section>

      {/* Themed shelves */}
      <section className="mx-auto max-w-7xl px-4 space-y-4">
        {SHELVES.map((s) =>
          shelves[s.q]?.length ? (
            <ProductRow
              key={s.q}
              title={s.title}
              products={shelves[s.q]}
              seeAllHref={`/category/${encodeURIComponent(s.q)}`}
            />
          ) : null
        )}
      </section>

      {/* Browse all */}
      <section className="mx-auto max-w-7xl px-4">
        <div className="bg-white dark:bg-[#160030] rounded-xl p-4 shadow-sm border border-violet-100 dark:border-violet-900/40">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold">Explore the mall</h2>
            <span className="text-xs opacity-70">{products?.length ?? "—"} items</span>
          </div>
          <CategoryFilter categories={categories} active={active} onChange={setActive} />
          {products === null ? <GridSkeleton /> : <ProductGrid products={products} />}
        </div>
      </section>
    </div>
  );
}
