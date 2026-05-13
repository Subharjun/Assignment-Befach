"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import { Star, Sparkles } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { api } from "@/lib/api";
import type { Product } from "@/lib/types";
import { useCart } from "@/store/cart";
import { useChat } from "@/store/chat";
import ProductGrid from "@/components/ProductGrid";
import { GridSkeleton } from "@/components/Skeleton";

export default function ProductDetail() {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [related, setRelated] = useState<Product[] | null>(null);
  const add = useCart((s) => s.add);
  const setChatOpen = useChat((s) => s.setOpen);
  const { getToken } = useAuth();

  useEffect(() => {
    if (!id) return;
    void api.getProduct(id).then(setProduct).catch(() => setProduct(null));
    void api.related(id, 8).then(setRelated).catch(() => setRelated([]));
    // best-effort history push
    void (async () => {
      try {
        const t = await getToken();
        if (t) await api.pushHistory(id, t);
      } catch {}
    })();
  }, [id, getToken]);

  if (!product) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-6 space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          <div className="aspect-square shimmer animate-shimmer rounded-2xl" />
          <div className="space-y-3">
            <div className="h-7 w-2/3 shimmer animate-shimmer rounded" />
            <div className="h-4 w-full shimmer animate-shimmer rounded" />
            <div className="h-4 w-5/6 shimmer animate-shimmer rounded" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 space-y-10">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="relative aspect-square rounded-2xl overflow-hidden bg-black/5 dark:bg-white/5">
          <Image src={product.image_url} alt={product.title} fill className="object-cover" />
        </div>
        <div>
          <div className="text-sm uppercase tracking-wide opacity-60">{product.brand}</div>
          <h1 className="mt-1 text-2xl sm:text-3xl font-semibold">{product.title}</h1>
          <div className="mt-2 flex items-center gap-2 text-sm">
            <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
            {product.rating.toFixed(1)} <span className="opacity-60">({product.rating_count} ratings)</span>
          </div>
          <div className="mt-4 text-3xl font-semibold">
            ₹{product.price.toLocaleString("en-IN")}
          </div>
          <p className="mt-4 text-sm leading-relaxed opacity-90">{product.description}</p>

          <div className="mt-6 flex gap-3">
            <button
              onClick={() => add(product)}
              className="px-5 py-2.5 rounded-full bg-yellow-400 hover:bg-yellow-500 text-neutral-900 font-medium transition"
            >
              Add to cart
            </button>
            <button
              onClick={() => setChatOpen(true)}
              className="px-5 py-2.5 rounded-full bg-orange-400 hover:bg-orange-500 text-neutral-900 font-medium transition inline-flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4" /> Ask Maya about this
            </button>
          </div>
        </div>
      </div>

      <section>
        <h2 className="text-lg font-semibold mb-3">You may also like</h2>
        {related === null ? <GridSkeleton n={4} /> : <ProductGrid products={related} />}
      </section>
    </div>
  );
}
