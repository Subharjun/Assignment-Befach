"use client";
import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import ProductGrid from "@/components/ProductGrid";
import { GridSkeleton } from "@/components/Skeleton";

export default function SearchPage() {
  const params = useSearchParams();
  const q = params.get("q") ?? "";
  const [results, setResults] = useState<Product[] | null>(null);

  useEffect(() => {
    if (!q) {
      setResults([]);
      return;
    }
    setResults(null);
    void api
      .semanticSearch(q, 16)
      .then(setResults)
      .catch(() => setResults([]));
  }, [q]);

  return (
    <div className="mx-auto max-w-7xl px-4 py-6">
      <h1 className="text-xl font-semibold mb-1">Semantic search</h1>
      <p className="text-sm opacity-70 mb-5">
        Showing results for <span className="font-medium">"{q}"</span>
      </p>
      {results === null ? <GridSkeleton /> : <ProductGrid products={results} />}
    </div>
  );
}
