"use client";
import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import ProductGrid from "@/components/ProductGrid";
import { GridSkeleton } from "@/components/Skeleton";

const SORTS = [
  { value: "rating", label: "Featured" },
  { value: "price_asc", label: "Price: Low to High" },
  { value: "price_desc", label: "Price: High to Low" },
];

export default function CategoryPage() {
  const { name } = useParams<{ name: string }>();
  const router = useRouter();
  const params = useSearchParams();
  const category = decodeURIComponent(name);

  const page = Math.max(1, Number(params.get("page") ?? 1));
  const sort = params.get("sort") ?? "rating";
  const pageSize = 24;

  const [items, setItems] = useState<Product[] | null>(null);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    setItems(null);
    void api
      .listProducts(category, page, pageSize, sort)
      .then((r) => {
        setItems(r.items);
        setTotal(r.total);
      })
      .catch(() => setItems([]));
  }, [category, page, sort]);

  const pages = useMemo(() => Math.max(1, Math.ceil(total / pageSize)), [total]);

  function update(next: Partial<{ page: number; sort: string }>) {
    const p = new URLSearchParams(params.toString());
    if (next.page !== undefined) p.set("page", String(next.page));
    if (next.sort !== undefined) p.set("sort", next.sort);
    router.push(`/category/${encodeURIComponent(category)}?${p.toString()}`);
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <div className="flex items-baseline justify-between mb-4 flex-wrap gap-2">
        <div>
          <div className="text-xs uppercase tracking-wide opacity-70">Category</div>
          <h1 className="text-2xl font-semibold">{category}</h1>
          {items && (
            <div className="text-xs opacity-70 mt-0.5">
              {total.toLocaleString("en-IN")} results
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm">
          <label className="opacity-70">Sort by</label>
          <select
            value={sort}
            onChange={(e) => update({ sort: e.target.value, page: 1 })}
            className="rounded-md border border-black/10 dark:border-white/10 bg-white dark:bg-neutral-900 px-2 py-1.5"
          >
            {SORTS.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="bg-white dark:bg-neutral-900 rounded-md p-4 shadow-sm border border-black/5 dark:border-white/10">
        {items === null ? <GridSkeleton n={12} /> : <ProductGrid products={items} />}
      </div>

      {items && pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-1 text-sm">
          <button
            onClick={() => update({ page: Math.max(1, page - 1) })}
            disabled={page === 1}
            className="px-3 py-1.5 rounded border border-black/10 dark:border-white/10 disabled:opacity-40 bg-white dark:bg-neutral-900"
          >
            Previous
          </button>
          {pageNumbers(page, pages).map((p, i) =>
            p === "…" ? (
              <span key={i} className="px-2 opacity-60">
                …
              </span>
            ) : (
              <button
                key={i}
                onClick={() => update({ page: p as number })}
                className={
                  "px-3 py-1.5 rounded border border-black/10 dark:border-white/10 " +
                  (p === page
                    ? "bg-orange-400 text-neutral-900 font-medium"
                    : "bg-white dark:bg-neutral-900")
                }
              >
                {p}
              </button>
            )
          )}
          <button
            onClick={() => update({ page: Math.min(pages, page + 1) })}
            disabled={page === pages}
            className="px-3 py-1.5 rounded border border-black/10 dark:border-white/10 disabled:opacity-40 bg-white dark:bg-neutral-900"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function pageNumbers(current: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const out: (number | "…")[] = [1];
  const left = Math.max(2, current - 1);
  const right = Math.min(total - 1, current + 1);
  if (left > 2) out.push("…");
  for (let i = left; i <= right; i++) out.push(i);
  if (right < total - 1) out.push("…");
  out.push(total);
  return out;
}
