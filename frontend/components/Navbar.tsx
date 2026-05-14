"use client";
import Link from "next/link";
import { ShoppingCart, MapPin, ChevronDown, Mic, Moon, Sun } from "lucide-react";
import { SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import { useEffect, useState } from "react";
import { useCart } from "@/store/cart";
import { useChat } from "@/store/chat";
import { useTheme } from "@/store/theme";
import SearchBar from "./SearchBar";

const QUICK_CATS = [
  "All",
  "Today's Deals",
  "Laptops",
  "Mobiles",
  "Audio",
  "Monitors",
  "Accessories",
  "Footwear",
  "Clothing",
  "Beauty",
  "Books",
  "Kitchen",
  "Furniture",
];

export default function Navbar() {
  const cartCount = useCart((s) => s.count());
  const setVoiceOpen = useChat((s) => s.setOpen);
  const { theme, toggle } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <header className="sticky top-0 z-30 text-white">
      {/* Primary bar */}
      <div className="bg-[#1e0048]">
        <div className="mx-auto max-w-7xl px-3 h-14 flex items-center gap-2">
          <Link href="/" className="px-2 py-1 rounded hover:ring-1 hover:ring-white/40 shrink-0">
            <span className="text-xl font-bold tracking-tight">
              <span className="text-violet-300">Maya</span>Mall
            </span>
            <span className="text-[10px] opacity-60">.in</span>
          </Link>

          <button className="hidden md:flex flex-col items-start px-2 py-1 rounded hover:ring-1 hover:ring-white/40 leading-tight shrink-0">
            <span className="text-[11px] opacity-80 flex items-center gap-1">
              <MapPin className="w-3 h-3" /> Deliver to
            </span>
            <span className="text-sm font-semibold">India</span>
          </button>

          <SearchBar />

          <button
            onClick={() => setVoiceOpen(true)}
            className="hidden sm:inline-flex items-center gap-2 px-3 py-2 rounded-md bg-violet-500 hover:bg-violet-400 text-white font-medium transition shrink-0"
          >
            <Mic className="w-4 h-4" /> Ask Maya
          </button>

          <button
            onClick={toggle}
            aria-label="Toggle theme"
            className="hidden sm:grid place-items-center w-9 h-9 rounded hover:ring-1 hover:ring-white/40"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>

          <SignedOut>
            <SignInButton>
              <button className="flex flex-col items-start px-2 py-1 rounded hover:ring-1 hover:ring-white/40 leading-tight">
                <span className="text-[11px] opacity-80">Hello, sign in</span>
                <span className="text-sm font-semibold flex items-center">
                  Account <ChevronDown className="w-3 h-3 ml-0.5" />
                </span>
              </button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <div className="px-1 py-1 rounded hover:ring-1 hover:ring-white/40">
              <UserButton />
            </div>
          </SignedIn>

          <Link
            href="/cart"
            className="flex items-end gap-1 px-2 py-1 rounded hover:ring-1 hover:ring-white/40"
            aria-label="Cart"
          >
            <div className="relative">
              <ShoppingCart className="w-7 h-7" />
              <span className="absolute -top-1 left-3 text-violet-300 text-sm font-bold">
                {mounted ? cartCount : 0}
              </span>
            </div>
            <span className="hidden sm:inline text-sm font-semibold pb-0.5">Cart</span>
          </Link>
        </div>
      </div>

      {/* Secondary nav strip */}
      <nav className="bg-[#2d0060] text-sm">
        <div className="mx-auto max-w-7xl px-2 h-10 flex items-center gap-1 overflow-x-auto">
          {QUICK_CATS.map((c) => (
            <Link
              key={c}
              href={
                c === "All"
                  ? "/"
                  : c === "Today's Deals"
                    ? "/search?q=deals"
                    : `/category/${encodeURIComponent(c)}`
              }
              className="px-2 py-1 rounded hover:ring-1 hover:ring-white/40 whitespace-nowrap"
            >
              {c}
            </Link>
          ))}
        </div>
      </nav>
    </header>
  );
}
