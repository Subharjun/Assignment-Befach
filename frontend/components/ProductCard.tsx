"use client";
import Link from "next/link";
import Image from "next/image";
import { Star } from "lucide-react";
import type { Product } from "@/lib/types";
import { useCart } from "@/store/cart";

export default function ProductCard({ product }: { product: Product }) {
  const add = useCart((s) => s.add);
  const mrp = Math.round(product.price * 1.18);
  const off = Math.round(((mrp - product.price) / mrp) * 100);

  return (
    <div className="group flex flex-col rounded-xl bg-white dark:bg-[#160030] border border-violet-100 dark:border-violet-900/40 hover:shadow-lg hover:border-violet-300 dark:hover:border-violet-700 transition animate-fade-in-up overflow-hidden">
      <Link href={`/products/${product.slug}`} className="block">
        <div className="relative aspect-square bg-white dark:bg-[#0f0020]">
          <Image
            src={product.image_url}
            alt={product.title}
            fill
            sizes="(max-width: 768px) 50vw, 25vw"
            className="object-contain p-4 group-hover:scale-105 transition duration-300"
          />
          {off >= 10 && (
            <span className="absolute top-2 left-2 text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-violet-600 text-white">
              {off}% off
            </span>
          )}
        </div>
      </Link>

      <div className="p-3 flex-1 flex flex-col">
        <Link href={`/products/${product.slug}`}>
          <h3 className="text-sm font-medium text-violet-700 dark:text-violet-300 hover:underline line-clamp-2 min-h-[2.5rem]">
            {product.title}
          </h3>
        </Link>

        <div className="mt-1 flex items-center gap-1 text-xs">
          <Stars value={product.rating} />
          <span className="text-violet-600 dark:text-violet-400 opacity-80">
            {product.rating_count.toLocaleString("en-IN")}
          </span>
        </div>

        <div className="mt-2 flex items-baseline gap-2">
          <span className="text-[11px] align-top opacity-70">₹</span>
          <span className="text-xl font-semibold">
            {product.price.toLocaleString("en-IN")}
          </span>
          <span className="text-xs opacity-50 line-through">
            ₹{mrp.toLocaleString("en-IN")}
          </span>
        </div>

        <div className="text-[11px] opacity-60 mt-0.5">
          FREE delivery <span className="font-semibold">tomorrow</span>
        </div>

        {(product.stock ?? 0) < 20 && (product.stock ?? 0) > 0 && (
          <div className="text-[11px] text-red-500 dark:text-red-400 mt-1">
            Only {product.stock} left in stock.
          </div>
        )}

        <button
          onClick={() => add(product)}
          className="mt-auto pt-3 w-full text-xs py-1.5 rounded-full bg-violet-600 hover:bg-violet-500 text-white font-medium transition"
        >
          Add to cart
        </button>
      </div>
    </div>
  );
}

function Stars({ value }: { value: number }) {
  const full = Math.floor(value);
  const half = value - full >= 0.5;
  return (
    <div className="flex items-center" aria-label={`Rated ${value} out of 5`}>
      {Array.from({ length: 5 }).map((_, i) => {
        const filled = i < full || (i === full && half);
        return (
          <Star
            key={i}
            className={`w-3.5 h-3.5 ${
              filled ? "fill-yellow-400 text-yellow-400" : "text-neutral-300 dark:text-neutral-700"
            }`}
          />
        );
      })}
    </div>
  );
}
