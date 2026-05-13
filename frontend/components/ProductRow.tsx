import Link from "next/link";
import Image from "next/image";
import type { Product } from "@/lib/types";

export default function ProductRow({
  title,
  products,
  seeAllHref,
}: {
  title: string;
  products: Product[];
  seeAllHref?: string;
}) {
  return (
    <section className="bg-white dark:bg-neutral-900 rounded-md p-4 shadow-sm border border-black/5 dark:border-white/10">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-lg font-semibold">{title}</h2>
        {seeAllHref && (
          <Link href={seeAllHref} className="text-sm text-blue-700 dark:text-blue-300 hover:underline">
            See all
          </Link>
        )}
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {products.slice(0, 5).map((p) => (
          <Link
            key={p.slug}
            href={`/products/${p.slug}`}
            className="block rounded hover:bg-neutral-50 dark:hover:bg-white/5 p-2 transition"
          >
            <div className="relative aspect-square bg-white rounded overflow-hidden">
              <Image
                src={p.image_url}
                alt={p.title}
                fill
                sizes="200px"
                className="object-contain p-2"
              />
            </div>
            <div className="mt-2 text-xs line-clamp-2 min-h-[2rem]">{p.title}</div>
            <div className="mt-0.5 text-sm font-semibold">
              ₹{p.price.toLocaleString("en-IN")}
            </div>
          </Link>
        ))}
      </div>
    </section>
  );
}
