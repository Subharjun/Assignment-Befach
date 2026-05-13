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
      <section className="relative h-48 sm:h-72 overflow-hidden bg-gradient-to-r from-[#131921] via-[#232f3e] to-[#37475a] text-white">
        <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_20%_50%,rgba(255,153,0,0.6),transparent_50%)]" />
        <div className="mx-auto max-w-7xl px-4 h-full flex items-center justify-between relative">
          <div className="max-w-xl">
            <div className="text-xs uppercase tracking-widest text-orange-300">AI Shopping — voice first</div>
            <h1 className="mt-2 text-2xl sm:text-4xl font-semibold leading-tight">
              Tell Maya what you need.<br/> She'll walk you to it.
            </h1>
            <button
              onClick={() => setVoiceOpen(true)}
              className="mt-4 inline-flex items-center gap-2 bg-orange-400 hover:bg-orange-500 text-neutral-900 px-4 py-2 rounded-full font-medium"
            >
              <Mic className="w-4 h-4" /> Talk to Maya
            </button>
          </div>
          <div className="hidden md:block text-7xl opacity-30">🛍️</div>
        </div>
      </section>

      {/* Category tiles */}
      <section className="mx-auto max-w-7xl px-4 grid grid-cols-2 lg:grid-cols-4 gap-3">
        {tiles.map((t) => (
          <a
            key={t.q}
            href={`/category/${encodeURIComponent(t.q)}`}
            className="bg-white dark:bg-neutral-900 rounded-md p-4 shadow-sm border border-black/5 dark:border-white/10 hover:shadow-lg transition"
          >
            <div className="font-semibold text-sm sm:text-base">{t.title}</div>
            <div className="relative w-full aspect-[4/3] mt-3 rounded overflow-hidden bg-neutral-100 dark:bg-neutral-800">
              <img src={t.img} alt={t.title} className="w-full h-full object-cover" />
            </div>
            <div className="mt-2 text-xs text-blue-700 dark:text-blue-300 hover:underline">Shop now</div>
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
        <div className="bg-white dark:bg-neutral-900 rounded-md p-4 shadow-sm border border-black/5 dark:border-white/10">
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
