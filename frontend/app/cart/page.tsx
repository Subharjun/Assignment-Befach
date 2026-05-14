"use client";
import Image from "next/image";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { useCart } from "@/store/cart";

export default function CartPage() {
  const { items, setQty, remove, subtotal } = useCart();

  if (items.length === 0) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-20 text-center space-y-3">
        <h1 className="text-2xl font-semibold">Your cart is empty</h1>
        <p className="opacity-70">Discover something Maya picked for you.</p>
        <Link
          href="/"
          className="inline-block mt-2 px-4 py-2 rounded-full bg-violet-600 hover:bg-violet-500 text-white font-medium transition"
        >
          Continue shopping
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 grid grid-cols-1 lg:grid-cols-[1fr_360px] gap-8">
      <div className="space-y-4">
        {items.map((i) => (
          <div
            key={i.slug}
            className="flex gap-4 p-3 rounded-xl border border-black/10 dark:border-white/10"
          >
            <div className="relative w-24 h-24 rounded-lg overflow-hidden bg-black/5 dark:bg-white/5 shrink-0">
              <Image src={i.image_url} alt={i.title} fill className="object-cover" sizes="96px" />
            </div>
            <div className="flex-1">
              <Link href={`/products/${i.slug}`} className="font-medium hover:underline">
                {i.title}
              </Link>
              <div className="mt-1 text-sm opacity-70">
                ₹{i.price.toLocaleString("en-IN")}
              </div>
              <div className="mt-2 flex items-center gap-2">
                <button
                  onClick={() => setQty(i.slug, i.qty - 1)}
                  className="w-7 h-7 rounded-full bg-black/5 dark:bg-white/10"
                >
                  −
                </button>
                <span className="w-6 text-center">{i.qty}</span>
                <button
                  onClick={() => setQty(i.slug, i.qty + 1)}
                  className="w-7 h-7 rounded-full bg-black/5 dark:bg-white/10"
                >
                  +
                </button>
                <button
                  onClick={() => remove(i.slug)}
                  className="ml-3 text-sm opacity-70 hover:text-red-600 inline-flex items-center gap-1"
                >
                  <Trash2 className="w-4 h-4" /> Remove
                </button>
              </div>
            </div>
            <div className="font-semibold">
              ₹{(i.price * i.qty).toLocaleString("en-IN")}
            </div>
          </div>
        ))}
      </div>

      <aside className="h-fit p-5 rounded-2xl border border-black/10 dark:border-white/10 sticky top-20">
        <h2 className="text-lg font-semibold mb-3">Order summary</h2>
        <div className="flex justify-between text-sm">
          <span className="opacity-70">Subtotal</span>
          <span>₹{subtotal().toLocaleString("en-IN")}</span>
        </div>
        <div className="flex justify-between text-sm mt-1">
          <span className="opacity-70">Shipping</span>
          <span>Free</span>
        </div>
        <div className="h-px bg-black/10 dark:bg-white/10 my-3" />
        <div className="flex justify-between font-semibold">
          <span>Total</span>
          <span>₹{subtotal().toLocaleString("en-IN")}</span>
        </div>
        <button className="mt-4 w-full py-2.5 rounded-full bg-violet-600 hover:bg-violet-500 text-white font-medium">
          Proceed to checkout
        </button>
        <p className="text-[11px] opacity-60 mt-2 text-center">
          Checkout flow is a stub in this scaffold.
        </p>
      </aside>
    </div>
  );
}
